"""Externalize current shot mesh/texture data while retaining local editable shading.

Run in Blender CLI with -- migrate|verify|render-source|render-candidate|verify-published.
All generated data stays in the project; migration writes a candidate only.
"""
import gzip
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
SHOT = ROOT / '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
CACHE = ROOT / '07_pipeline/cache/shot_external_links_20261006'
REVIEW = ROOT / '06_review/shot_external_links_20261006'
CANDIDATE = CACHE / 'drop_sq010_sh010_shot.blend'
LIBRARY = ROOT / '02_assets/library/classroom_geometry.blend'
FALLBACK = ROOT / '02_assets/Texture/classroom_links'
BASELINE = CACHE / 'baseline.json.gz'
MANIFEST = REVIEW / 'dependencies.json'


def digest(path):
    """Input path; return SHA256 using bounded file reads."""
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def dump(path, value):
    """Input project path and JSON data; write UTF-8, optionally gzip compressed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')
    path.write_bytes(gzip.compress(data) if path.suffix == '.gz' else data)


def read(path):
    """Input JSON/gzip path; return decoded data."""
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def plain(value):
    """Input Blender value; return stable JSON scalar, sequence or ID reference."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bpy.types.ID):
        return {'id': value.name, 'type': value.bl_rna.identifier}
    if hasattr(value, 'to_dict'):
        return {k: plain(v) for k, v in value.to_dict().items()}
    try:
        return [plain(v) for v in value]
    except TypeError:
        return getattr(value, 'name', str(value))


def scalars(block, excluded=()):
    """Input RNA block; return writable scalar/array/ID properties, excluding runtime fields."""
    result = {}
    for prop in block.bl_rna.properties:
        key = prop.identifier
        if key in {'rna_type', *excluded} or prop.is_readonly or prop.type == 'COLLECTION':
            continue
        try:
            value = getattr(block, key)
        except (AttributeError, TypeError):
            continue
        if prop.type != 'POINTER' or value is None or isinstance(value, bpy.types.ID):
            result[key] = plain(value)
    return result


def custom_properties(block):
    """Input RNA block; return supported custom properties, or an empty mapping."""
    try:
        return plain(dict(block.items()))
    except TypeError:
        return {}


def drivers(block):
    """Input animated ID; return action assignment and complete driver targets/expressions."""
    animation = getattr(block, 'animation_data', None)
    if not animation:
        return None
    return {'action': plain(animation.action), 'drivers': [
        {'path': f.data_path, 'index': f.array_index, 'type': f.driver.type,
         'expression': f.driver.expression, 'variables': [
             {'name': v.name, 'type': v.type, 'targets': [scalars(t) for t in v.targets]}
             for v in f.driver.variables]} for f in animation.drivers]}


def tree_state(tree):
    """Input node tree; return node settings, sockets, ramps, links, interfaces and drivers."""
    if tree is None:
        return None
    nodes = []
    for node in tree.nodes:
        row = {'props': scalars(node), 'custom': plain(dict(node.items())),
               'inputs': [scalars(s) for s in node.inputs],
               'outputs': [scalars(s) for s in node.outputs]}
        ramp = getattr(node, 'color_ramp', None)
        if ramp:
            row['ramp'] = {'settings': scalars(ramp), 'elements': [scalars(e) for e in ramp.elements]}
        mapping = getattr(node, 'mapping', None)
        if mapping and hasattr(mapping, 'curves'):
            row['mapping'] = {'settings': scalars(mapping),
                              'curves': [[scalars(p) for p in c.points] for c in mapping.curves]}
        nodes.append(row)
    links = [[l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier]
             for l in tree.links]
    interface = getattr(tree, 'interface', None)
    state = {'nodes': nodes, 'links': links, 'drivers': drivers(tree),
             'custom': plain(dict(tree.items())),
             'interface': [scalars(i) for i in interface.items_tree] if interface else []}
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def mesh_state(mesh):
    """Input base mesh; hash geometry, every attribute, UV state and face material indices."""
    h = hashlib.sha256()
    metadata = {'vertices': len(mesh.vertices), 'edges': len(mesh.edges),
                'loops': len(mesh.loops), 'polygons': len(mesh.polygons),
                'props': scalars(mesh, ('materials', 'animation_data', 'use_fake_user')),
                'custom': plain(dict(mesh.items())),
                'uvs': [(u.name, u.active_render, u.active_clone) for u in mesh.uv_layers]}
    h.update(json.dumps(metadata, sort_keys=True).encode())
    for collection, fields in [(mesh.vertices, ('co',)), (mesh.edges, ('vertices',)),
                               (mesh.loops, ('vertex_index', 'edge_index')),
                               (mesh.polygons, ('loop_start', 'loop_total', 'material_index', 'use_smooth'))]:
        if not collection:
            continue
        for field in fields:
            prop = collection[0].bl_rna.properties[field]
            arr = np.empty(len(collection) * max(1, prop.array_length),
                           dtype=np.float32 if prop.type == 'FLOAT' else np.int32)
            collection.foreach_get(field, arr)
            h.update(arr.tobytes())
    for attribute in sorted(mesh.attributes, key=lambda a: a.name):
        h.update(json.dumps([attribute.name, attribute.domain, attribute.data_type]).encode())
        if not attribute.data:
            continue
        for prop in attribute.data[0].bl_rna.properties:
            if prop.identifier == 'rna_type':
                continue
            if prop.type in {'FLOAT', 'INT', 'BOOLEAN'}:
                arr = np.empty(len(attribute.data) * max(1, prop.array_length),
                               dtype=np.float32 if prop.type == 'FLOAT' else np.int32)
                attribute.data.foreach_get(prop.identifier, arr)
                h.update(arr.tobytes())
            elif prop.type == 'STRING':
                h.update(json.dumps([getattr(v, prop.identifier) for v in attribute.data]).encode())
    return h.hexdigest()


def snapshot():
    """Input loaded shot; return protected geometry, shading, objects, scenes and animation."""
    objects = {}
    for ob in bpy.data.objects:
        objects[ob.name] = {'type': ob.type, 'data': ob.data.name if ob.data else None,
            'props': scalars(ob, ('active_material', 'active_material_index', 'mode')),
            'matrix_basis': plain(ob.matrix_basis), 'custom': plain(dict(ob.items())),
            'materials': [slot.material.name if slot.material else None for slot in ob.material_slots],
            'modifiers': [dict(props=scalars(m), custom=custom_properties(m)) for m in ob.modifiers],
            'constraints': [scalars(c) for c in ob.constraints], 'drivers': drivers(ob)}
    scenes = {}
    for scene in bpy.data.scenes:
        scenes[scene.name] = {'props': scalars(scene), 'render': scalars(scene.render),
            'cycles': scalars(scene.cycles), 'view': scalars(scene.view_settings),
            'world': scene.world.name if scene.world else None,
            'camera': scene.camera.name if scene.camera else None,
            'objects': sorted(o.name for o in scene.objects),
            'tree': tree_state(getattr(scene, 'compositing_node_group', getattr(scene, 'node_tree', None)))}
        scenes[scene.name]['render']['filepath'] = ('//' if scene.render.filepath == '//'
            else bpy.path.abspath(scene.render.filepath).replace('\\', '/'))
    actions = {}
    for action in bpy.data.actions:
        curves = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        curves.append({'path': curve.data_path, 'index': curve.array_index,
                            'keys': [scalars(p) for p in curve.keyframe_points]})
        actions[action.name] = curves
    return {'meshes': {m.name: mesh_state(m) for m in bpy.data.meshes}, 'objects': objects,
            'materials': {m.name: {'props': scalars(m), 'tree': tree_state(m.node_tree),
                                  'custom': plain(dict(m.items()))} for m in bpy.data.materials
                          if not m.name.startswith('__External geometry slot')},
            'groups': {g.name: tree_state(g) for g in bpy.data.node_groups},
            'worlds': {w.name: {'props': scalars(w), 'tree': tree_state(w.node_tree)} for w in bpy.data.worlds},
            'cameras': {c.name: scalars(c) for c in bpy.data.cameras},
            'lights': {l.name: scalars(l) for l in bpy.data.lights},
            'collections': {c.name: {'objects': sorted(o.name for o in c.objects),
                'children': sorted(v.name for v in c.children), 'props': scalars(c),
                'custom': plain(dict(c.items()))} for c in bpy.data.collections},
            'scenes': scenes, 'actions': actions}


def texture_destination(image, payload_hash):
    """Input packed image and SHA256; choose matching project file, preserving existing differences."""
    original = image.filepath.replace('\\', '/')
    resolved = Path(bpy.path.abspath(image.filepath)).resolve()
    options = [resolved]
    if '02_assets/' in original:
        options.insert(0, ROOT / '02_assets' / original.split('02_assets/', 1)[1])
    for path in options:
        if path.is_relative_to(ROOT) and path.is_file() and digest(path) == payload_hash:
            return path, False
    suffix = Path(original).suffix.lower() or '.png'
    stem = Path(original).stem or image.name.split('.')[0]
    path = FALLBACK / f'{stem}_{payload_hash[:16]}{suffix}'
    if path.exists():
        assert digest(path) == payload_hash, f'Conflicting extraction destination: {path}'
    return path, not path.exists()


def externalize_images():
    """Input current images; extract exact packed bytes and switch to relative external paths."""
    result, known = [], {}
    bpy.data.use_autopack = False
    for image in bpy.data.images:
        packed_files = list(image.packed_files)
        if not packed_files:
            continue
        assert len(packed_files) == 1, f'Multi-tile image requires separate handling: {image.name}'
        packed = packed_files[0].packed_file
        data = packed.data
        content_hash = hashlib.sha256(data).hexdigest()
        if content_hash in known:
            path, created = known[content_hash], False
        else:
            path, created = texture_destination(image, content_hash)
            if created:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            assert digest(path) == content_hash
            known[content_hash] = path
        row = {'image': image.name, 'original_path': image.filepath, 'sha256': content_hash,
               'bytes': len(data), 'path': path.relative_to(ROOT).as_posix(), 'created': created,
               'colorspace': image.colorspace_settings.name, 'alpha_mode': image.alpha_mode,
               'source': 'Exact packed payload from current shot; prior asset provenance retained'}
        image.unpack(method='REMOVE')
        image.filepath = bpy.path.relpath(str(path), start=str(SHOT.parent))
        result.append(row)
        del data
    return result


def externalize_meshes():
    """Input current meshes; write linked geometry library and bind original local materials to objects."""
    originals = list(bpy.data.meshes)
    assert not any(m.shape_keys or m.animation_data for m in originals), 'Animated mesh data requires overrides.'
    objects = [ob for ob in bpy.data.objects if ob.type == 'MESH']
    effective = {ob: [slot.material for slot in ob.material_slots] for ob in objects}
    placeholder = bpy.data.materials.new('__External geometry slot')
    # Local OBJECT slots retain all original shader bindings; library has only lightweight slot holders.
    for ob, materials in effective.items():
        for slot, material in zip(ob.material_slots, materials):
            slot.link = 'OBJECT'
            slot.material = material
    for mesh in originals:
        for index in range(len(mesh.materials)):
            mesh.materials[index] = placeholder
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    assert not LIBRARY.exists(), 'Existing library must be explicitly merged instead of overwritten.'
    bpy.data.libraries.write(str(LIBRARY), set(originals), fake_user=True, compress=True, path_remap='RELATIVE_ALL')
    with bpy.data.libraries.load(str(LIBRARY), link=True) as (available, loaded):
        loaded.meshes = [m.name for m in originals]
    linked = {m.name: m for m in loaded.meshes}
    assert len(linked) == len(originals) and all(m.library for m in linked.values())
    for mesh in originals:
        mesh.user_remap(linked[mesh.name])
    for ob, materials in effective.items():
        assert ob.data.library
        for slot, material in zip(ob.material_slots, materials):
            slot.link = 'OBJECT'
            slot.material = material
    bpy.data.batch_remove(originals)
    if placeholder.users == 0:
        bpy.data.materials.remove(placeholder)
    for library in bpy.data.libraries:
        library.filepath = bpy.path.relpath(str(LIBRARY), start=str(SHOT.parent))
    return {'path': LIBRARY.relative_to(ROOT).as_posix(), 'sha256': digest(LIBRARY),
            'bytes': LIBRARY.stat().st_size, 'meshes': len(linked),
            'source': SHOT.relative_to(ROOT).as_posix(), 'license': 'Inherited asset provenance; no new source materials'}


def compare(expected, actual):
    """Input baseline/candidate snapshots; return changed top-level IDs, fail on any protected change."""
    changes = {}
    for family, values in expected.items():
        current = actual[family]
        bad = [key for key in set(values) | set(current) if values.get(key) != current.get(key)]
        if bad:
            changes[family] = sorted(bad)
    return changes


def shading_probe():
    """Input loaded candidate; actually edit and restore local shader values in board, desk and chair."""
    probes = []
    for token in ('Blackboard', 'KOKUYO', 'Chair'):
        mats = [m for m in bpy.data.materials if token.casefold() in m.name.casefold() and m.node_tree]
        assert mats, f'No shader material for {token}'
        material = mats[0]
        assert material.library is None and material.is_editable and material.node_tree.is_editable
        found = None
        for node in material.node_tree.nodes:
            for socket in node.inputs:
                if socket.is_linked or not hasattr(socket, 'default_value'):
                    continue
                old = socket.default_value
                if isinstance(old, float) and abs(old) < 1e6:
                    socket.default_value = old + .001
                    changed = abs(socket.default_value - old) > .00001
                    socket.default_value = old
                    if changed:
                        found = {'material': material.name, 'node': node.name, 'socket': socket.name}
                        break
            if found:
                break
        assert found, f'No writable float socket for {material.name}'
        probes.append(found)
    return probes


def verify(path, tag):
    """Input candidate/published path; reopen, check protected data, dependencies and live shader edits."""
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    baseline = read(BASELINE)
    actual = snapshot()
    changes = compare(baseline['snapshot'], actual)
    used_meshes = {row['data'] for row in baseline['snapshot']['objects'].values() if row['type'] == 'MESH'}
    retained_only_in_library = sorted(set(baseline['snapshot']['meshes']) - set(actual['meshes']) - used_meshes)
    if changes.get('meshes'):
        changes['meshes'] = [n for n in changes['meshes'] if n not in retained_only_in_library]
        if not changes['meshes']:
            del changes['meshes']
    if changes:
        dump(CACHE / f'{tag}_snapshot.json.gz', actual)
    manifest = read(MANIFEST)
    image_checks = []
    for row in manifest['textures']:
        image = bpy.data.images[row['image']]
        dest = Path(bpy.path.abspath(image.filepath)).resolve()
        image_checks.append(dest.is_file() and digest(dest) == row['sha256'] and not image.packed_file
                            and image.filepath.startswith('//')
                            and image.colorspace_settings.name == row['colorspace']
                            and image.alpha_mode == row['alpha_mode'])
    linked = [m for m in bpy.data.meshes if m.library]
    all_local = all(m.library is None and m.is_editable for m in bpy.data.materials
                    if not m.name.startswith('__External geometry slot'))
    local_groups = all(g.library is None and g.is_editable for g in bpy.data.node_groups)
    probes = shading_probe() if not changes else []
    result = {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size,
        'protected_changes': changes, 'all_texture_checks': all(image_checks),
        'texture_images': len(image_checks), 'linked_meshes': len(linked),
        'all_geometry_linked': len(linked) == len(used_meshes),
        'unreferenced_meshes_retained_in_library': retained_only_in_library,
        'materials_local_editable': all_local, 'node_groups_local_editable': local_groups,
        'shading_probes': probes, 'library': manifest['geometry'],
        'source_unchanged': digest(SHOT) == baseline['source_sha256'] if tag != 'published' else None}
    packed_names = {row['image'] for row in manifest['textures']}
    other_dependencies, unresolved = {}, []
    for image in bpy.data.images:
        if image.name in packed_names or image.source != 'FILE' or not image.filepath:
            continue
        dep = Path(bpy.path.abspath(image.filepath)).resolve()
        if dep.is_file() and dep.is_relative_to(ROOT):
            key = dep.relative_to(ROOT).as_posix()
            if key not in other_dependencies:
                other_dependencies[key] = {'path': key, 'bytes': dep.stat().st_size, 'sha256': digest(dep)}
        elif not image.packed_file:
            unresolved.append({'image': image.name, 'path': image.filepath})
    result['other_external_dependencies'] = list(other_dependencies.values())
    result['existing_unresolved_image_dependencies'] = unresolved
    result['geometry_library_hash_matches'] = digest(LIBRARY) == manifest['geometry']['sha256']
    result['passed'] = (not changes and all(image_checks) and result['all_geometry_linked'] and all_local
                        and local_groups and bool(probes) and result['geometry_library_hash_matches'])
    dump(REVIEW / f'{tag}_verification.json', result)
    print('VERIFY', json.dumps({k: result[k] for k in ('passed', 'bytes', 'protected_changes',
          'texture_images', 'linked_meshes', 'materials_local_editable', 'node_groups_local_editable')},
          ensure_ascii=False), flush=True)
    assert result['passed'], 'Candidate verification failed; see protected_changes.'


def render(path, tag):
    """Input source/candidate; render identical temporary CPU preview without saving scene settings."""
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    scene = bpy.data.scenes['sq010_sh010']
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.seed = 0
    scene.render.resolution_x = 640
    scene.render.resolution_y = 270
    scene.render.resolution_percentage = 100
    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = 1
    scene.cycles.texture_limit_render = '1024'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(CACHE / f'{tag}.png')
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', tag, 'completed', flush=True)


def migrate():
    """Read current source, capture baseline, externalize exact dependencies and save candidate."""
    source_hash = digest(SHOT)
    bpy.ops.wm.open_mainfile(filepath=str(SHOT), load_ui=False)
    dump(BASELINE, {'source_sha256': source_hash, 'snapshot': snapshot()})
    textures = externalize_images()
    geometry = externalize_meshes()
    dump(MANIFEST, {'source': str(SHOT.relative_to(ROOT)), 'source_sha256': source_hash,
                    'textures': textures, 'geometry': geometry})
    changes = compare(read(BASELINE)['snapshot'], snapshot())
    dump(CACHE / 'in_memory_changes.json', changes)
    assert not changes, f'Protected changes during migration: {changes}'
    assert digest(SHOT) == source_hash, 'Source saved again; candidate must be rebuilt.'
    # Save As remaps formal-directory dependencies for an independently reopenable cache candidate.
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE), compress=True, relative_remap=True, check_existing=False)
    print('CANDIDATE', str(CANDIDATE), CANDIDATE.stat().st_size, flush=True)


def publish():
    """Publish validated candidate with path remapping and current-source hash protection."""
    baseline = read(BASELINE)
    assert read(REVIEW / 'candidate_verification.json')['passed']
    assert read(REVIEW / 'pixel_comparison.json')['passed']
    assert digest(SHOT) == baseline['source_sha256'], 'New user save detected; rebuild candidate.'
    backup = CACHE / 'source_before.blend'
    if not backup.exists():
        shutil.copy2(SHOT, backup)
    assert digest(backup) == baseline['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE), load_ui=False)
    assert digest(SHOT) == baseline['source_sha256'], 'New save during candidate reopen.'
    bpy.context.preferences.filepaths.save_version = 0
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(SHOT), compress=True, relative_remap=True, check_existing=False)
    except RuntimeError:
        # Blender may finish the @ stage but be denied the final Windows rename by a reader.
        stage = Path(str(SHOT) + '@')
        assert stage.is_file() and digest(SHOT) == baseline['source_sha256']
        os.replace(stage, SHOT)
    print('PUBLISHED', SHOT.stat().st_size, digest(SHOT), flush=True)


def prepare_library():
    """Make extracted library directly editable by adding one object per mesh in an authoring scene."""
    manifest = read(MANIFEST)
    assert digest(LIBRARY) == manifest['geometry']['sha256'], 'Geometry library changed outside migration.'
    baseline = read(BASELINE)['snapshot']
    bpy.ops.wm.open_mainfile(filepath=str(LIBRARY), load_ui=False)
    scene = bpy.context.scene
    scene.name = 'Classroom_Geometry_Edit'
    representatives = {}
    for name, row in baseline['objects'].items():
        if row['type'] == 'MESH':
            representatives.setdefault(row['data'], (name, row))
    memberships = {}
    for name, row in baseline['collections'].items():
        for ob in row['objects']:
            memberships.setdefault(ob, name)
    collections = {}
    for mesh in bpy.data.meshes:
        source_name, row = representatives.get(mesh.name, (None, None))
        group = memberships.get(source_name, 'Unplaced geometry')
        if group not in collections:
            collection = bpy.data.collections.new(group)
            scene.collection.children.link(collection)
            collections[group] = collection
        ob = bpy.data.objects.new(source_name or mesh.name, mesh)
        collections[group].objects.link(ob)
        if row:
            ob.matrix_world = Matrix(row['props']['matrix_world'])
        ob['shot_source_mesh'] = mesh.name
    actual = {m.name: mesh_state(m) for m in bpy.data.meshes}
    assert actual == baseline['meshes'], 'Library authoring scene changed geometry.'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(LIBRARY), compress=True, check_existing=False)
    manifest['geometry'].update(sha256=digest(LIBRARY), bytes=LIBRARY.stat().st_size,
                                authoring_scene=scene.name, authoring_objects=len(scene.objects))
    dump(MANIFEST, manifest)
    print('LIBRARY_EDIT_SCENE', len(scene.objects), LIBRARY.stat().st_size, flush=True)


def main():
    """Read CLI mode; dispatch candidate migration, independent verification or visual preview."""
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
    elif mode == 'prepare-library':
        prepare_library()
    elif mode == 'render-source':
        render(SHOT, 'source')
    elif mode == 'render-candidate':
        render(CANDIDATE, 'candidate')
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main()
