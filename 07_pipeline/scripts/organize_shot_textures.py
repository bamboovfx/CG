"""Audit current shot dependencies before organizing textures; run in Blender CLI."""
import bpy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '06_review/texture_cleanup_20261006'
SHOT = ROOT / '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
CHAIR = ROOT / '02_assets/work/school_chair.blend'


def digest(path):
    """Return SHA256 of a file using bounded memory."""
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def trees(tree, seen=None):
    """Yield nested shader trees once, including muted and disconnected nodes for safety."""
    seen = set() if seen is None else seen
    if not tree or tree.as_pointer() in seen:
        return
    seen.add(tree.as_pointer())
    yield tree
    for node in tree.nodes:
        if node.type == 'GROUP':
            yield from trees(node.node_tree, seen)


def inspect():
    """Return actual datablock users, image payload hashes and preserved scene settings."""
    materials = {slot.material for ob in bpy.data.objects for slot in ob.material_slots if slot.material}
    referenced = {}
    for material in materials:
        for tree in trees(material.node_tree):
            for node in tree.nodes:
                image = getattr(node, 'image', None)
                if image:
                    referenced.setdefault(image.name, set()).add(material.name)
    for world in bpy.data.worlds:
        for tree in trees(world.node_tree):
            for node in tree.nodes:
                image = getattr(node, 'image', None)
                if image:
                    referenced.setdefault(image.name, set()).add('WORLD:' + world.name)
    for scene in bpy.data.scenes:
        for tree in trees(getattr(scene, 'node_tree', None)):
            for node in tree.nodes:
                image = getattr(node, 'image', None)
                if image:
                    referenced.setdefault(image.name, set()).add('COMPOSITOR:' + scene.name)
    images = []
    for image in bpy.data.images:
        print('IMAGE', image.name, flush=True)
        path = Path(bpy.path.abspath(image.filepath, library=image.library)) if image.filepath else None
        packed = image.packed_file
        images.append(dict(name=image.name, path=str(path) if path else '', raw_path=image.filepath,
                           users=image.users, fake=image.use_fake_user, source=image.source,
                           colorspace=image.colorspace_settings.name,
                           packed=bool(packed), packed_size=packed.size if packed else 0,
                           sha256=digest(path) if path and path.is_file() else None,
                           exists=bool(path and path.is_file()), materials=sorted(referenced.get(image.name, []))))
    return dict(file=bpy.data.filepath, materials=[dict(name=m.name, users=m.users, fake=m.use_fake_user,
                assigned=m in materials) for m in bpy.data.materials], images=images,
                libraries=[l.filepath for l in bpy.data.libraries], objects=len(bpy.data.objects),
                scenes=[dict(name=s.name, camera=s.camera.name if s.camera else None, frame=s.frame_current,
                start=s.frame_start, end=s.frame_end, fps=s.render.fps, world=s.world.name if s.world else None,
                engine=s.render.engine) for s in bpy.data.scenes], actions=[a.name for a in bpy.data.actions])


def main():
    """Read shot and independent chair without saving, and emit an auditable inventory."""
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in [('shot', SHOT), ('chair', CHAIR)]:
        before = digest(path)
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
        data = inspect()
        data['sha256'] = before
        data['source_unchanged'] = digest(path) == before
        assert data['source_unchanged']
        (OUT / f'{name}_before.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(name, len(data['materials']), 'materials', len(data['images']), 'images', sum(bool(i['materials']) for i in data['images']), 'referenced', flush=True)


if __name__ == '__main__':
    main()
