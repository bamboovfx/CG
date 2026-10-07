"""Restore embedded shot geometry while preserving external textures and editable shading."""
import os
import shutil
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import externalize_shot_assets as audit

ROOT, SHOT = audit.ROOT, audit.SHOT
CACHE = ROOT / '07_pipeline/cache/shot_internal_geometry_20261007'
REVIEW = ROOT / '06_review/shot_internal_geometry_20261007'
CANDIDATE = CACHE / SHOT.name
BASELINE = CACHE / 'baseline.json.gz'
audit.CACHE = CACHE


def images_state():
    """Read loaded image metadata; return normalized paths and immutable interpretation settings."""
    return {im.name: {'path': Path(bpy.path.abspath(im.filepath)).resolve().as_posix() if im.filepath else '',
        'source': im.source, 'colorspace': im.colorspace_settings.name,
        'alpha_mode': im.alpha_mode, 'packed': len(im.packed_files)} for im in bpy.data.images}


def load_baseline():
    """Read protected source snapshot; normalize equivalent parent-directory texture paths."""
    baseline = audit.read(BASELINE)
    for row in baseline['images'].values():
        if row['path']:
            row['path'] = Path(row['path']).resolve().as_posix()
    return baseline


def geometry_probe():
    """Edit and restore one local vertex; return evidence without retaining a geometry change."""
    mesh = next(m for m in bpy.data.meshes if len(m.vertices))
    assert mesh.library is None and mesh.is_editable
    vertex = mesh.vertices[0]
    old = vertex.co.copy()
    vertex.co.x += .01
    assert vertex.co != old
    vertex.co = old
    return {'mesh': mesh.name, 'vertex': 0, 'edit_restored': vertex.co == old}


def migrate():
    """Read latest shot; snapshot and localize linked geometry in a protected candidate."""
    source_hash = audit.digest(SHOT)
    bpy.ops.wm.open_mainfile(filepath=str(SHOT), load_ui=False)
    if not BASELINE.exists() or audit.read(BASELINE)['source_sha256'] != source_hash:
        audit.dump(BASELINE, {'source_sha256': source_hash, 'snapshot': audit.snapshot(),
                              'images': images_state()})
    # ALL makes the scene's linked IDs local in one Blender operation, preserving shared users.
    # The loaded source links only meshes and their neutral material slot placeholders.
    assert all(m.library is None or m.name.startswith('__External geometry slot') for m in bpy.data.materials)
    bpy.ops.object.make_local(type='ALL')
    # Slot placeholders must also be local so geometry has no hidden blend-library dependency.
    for mat in list(bpy.data.materials):
        if mat.library:
            assert mat.name.startswith('__External geometry slot')
            mat.make_local()
    assert all(m.library is None for m in bpy.data.meshes)
    assert all(m.library is None for m in bpy.data.materials)
    for library in list(bpy.data.libraries):
        bpy.data.libraries.remove(library)
    assert not audit.compare(audit.read(BASELINE)['snapshot'], audit.snapshot())
    assert images_state() == load_baseline()['images']
    assert audit.digest(SHOT) == source_hash, 'User saved a new source; rebuild candidate.'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE), compress=True,
                              relative_remap=True, check_existing=False)
    print('CANDIDATE', CANDIDATE.stat().st_size, flush=True)


def verify(path, tag):
    """Independently reopen candidate/published shot; check data, texture hashes and actual edits."""
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    baseline = load_baseline()
    changes = audit.compare(baseline['snapshot'], audit.snapshot())
    actual_images = images_state()
    image_changes = {name: {'before': baseline['images'].get(name), 'after': actual_images.get(name)}
        for name in set(actual_images) | set(baseline['images'])
        if actual_images.get(name) != baseline['images'].get(name)}
    unchanged_images = not image_changes
    texture_checks = []
    for row in audit.read(ROOT / '06_review/shot_external_links_20261006/dependencies.json')['textures']:
        im = bpy.data.images[row['image']]
        dep = Path(bpy.path.abspath(im.filepath))
        texture_checks.append(dep.is_file() and audit.digest(dep) == row['sha256']
                              and not im.packed_files and im.filepath.startswith('//'))
    geometry = all(m.library is None and m.is_editable for m in bpy.data.meshes)
    shading = all(m.library is None and m.is_editable for m in bpy.data.materials)
    groups = all(g.library is None and g.is_editable for g in bpy.data.node_groups)
    result = {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
        'sha256': audit.digest(path), 'protected_changes': changes,
        'meshes': len(bpy.data.meshes), 'objects': len(bpy.data.objects),
        'original_materials': sum(not m.name.startswith('__External geometry slot') for m in bpy.data.materials),
        'node_groups': len(bpy.data.node_groups), 'libraries': len(bpy.data.libraries),
        'geometry_local_editable': geometry, 'materials_local_editable': shading,
        'node_groups_local_editable': groups, 'images_metadata_unchanged': unchanged_images,
        'image_metadata_changes': image_changes,
        'texture_images_checked': len(texture_checks), 'texture_hashes_passed': all(texture_checks),
        'geometry_probe': geometry_probe(), 'shading_probes': audit.shading_probe()}
    result['passed'] = (not changes and unchanged_images and all(texture_checks) and geometry
                        and shading and groups and not bpy.data.libraries and bool(result['shading_probes']))
    audit.dump(REVIEW / f'{tag}_verification.json', result)
    if changes:
        audit.dump(CACHE / f'{tag}_snapshot.json.gz', audit.snapshot())
    print('VERIFY', result, flush=True)
    assert result['passed'], 'Independent reopen verification failed.'


def publish():
    """Publish verified candidate after source hash guard; retain previous saved shot in cache."""
    baseline = audit.read(BASELINE)
    assert audit.read(REVIEW / 'candidate_verification.json')['passed']
    assert audit.read(REVIEW / 'pixel_comparison.json')['passed']
    assert audit.digest(SHOT) == baseline['source_sha256'], 'New source save detected.'
    backup = CACHE / 'source_before.blend'
    if not backup.exists():
        shutil.copy2(SHOT, backup)
    assert audit.digest(backup) == baseline['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE), load_ui=False)
    assert audit.digest(SHOT) == baseline['source_sha256'], 'New save during candidate reopen.'
    bpy.context.preferences.filepaths.save_version = 0
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(SHOT), compress=True,
                                  relative_remap=True, check_existing=False)
    except RuntimeError:
        stage = Path(str(SHOT) + '@')
        assert stage.is_file() and audit.digest(SHOT) == baseline['source_sha256']
        os.replace(stage, SHOT)
    print('PUBLISHED', SHOT.stat().st_size, audit.digest(SHOT), flush=True)


def main():
    """Read CLI mode; run migration, verification, preview or guarded publication sequentially."""
    CACHE.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[sys.argv.index('--') + 1]
    if mode == 'migrate':
        migrate()
    elif mode == 'verify':
        verify(CANDIDATE, 'candidate')
    elif mode == 'verify-published':
        verify(SHOT, 'published')
    elif mode == 'publish':
        publish()
    elif mode == 'render-source':
        audit.render(SHOT, 'source')
    elif mode == 'render-candidate':
        audit.render(CANDIDATE, 'candidate')
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main()
