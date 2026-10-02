"""将独立课椅改为同一可编辑集合的25个实例；共享材质读取实例Seed，生成不同木纹和金属损伤。

输入：当前正式镜头。输出：候选、独立重开检查与原位发布记录。
几何／UV／法线和所有控制对象摆位保持；只删除本轮明确被共享母资产取代的重复数据。
"""
from pathlib import Path
import hashlib
import json
import math as pmath
import sys
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replace_scene_chairs import TARGET, protected, layer_kind, PROPERTIES, scene_signature
from cleanup_wood_rear_stamp import geometry_digest
from chair_metal_blender import node, math, vector, bind, blend, clamp, placement
from wood_layers_blender import frame

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '07_pipeline/cache/chair_instances_20261001'
OUT = ROOT / '06_review/chair_instances_20261001'
CANDIDATE = WORK / 'chair_instances_candidate.blend'
MASTER = 'CHAIR / Shared editable asset'
EDIT = 'Chair_Asset_Edit'


def dump(path, value):
    """输入路径与可序列化证据，输出UTF-8 JSON；不写到工程以外。"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def digest_file(path):
    """输入文件，返回流式SHA256，用于覆盖保护和发布来源追溯。"""
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(data)
    return h.hexdigest()


def random_signal(tree, seed, salt):
    """输入稳定种子与用途盐值，返回0–1连续伪随机信号；逐实例相同且跨帧稳定。"""
    return math(tree, 'ADD', .5, math(tree, 'MULTIPLY', .5,
        math(tree, 'SINE', math(tree, 'ADD', math(tree, 'MULTIPLY', seed, .17331 + salt * .03127), salt * 2.719))))


def centred(tree, signal, extent):
    """输入0–1随机信号及半幅，返回正负半幅偏移，用于限制物理损伤位置。"""
    return math(tree, 'MULTIPLY', math(tree, 'SUBTRACT', signal, .5), extent * 2)


def combine(tree, values):
    """输入三轴常数／信号，返回向量接口；保留默认Combine XYZ节点标题。"""
    n = node(tree, 'ShaderNodeCombineXYZ', 'instance_vector')
    for axis, value in zip('XYZ', values): bind(tree, value, n.inputs[axis])
    return n.outputs[0]


def new_input(group, name, kind='NodeSocketFloat', default=0):
    """输入组、接口名／类型／默认值，新增公共接口并返回Group Input对应输出。"""
    s = group.interface.new_socket(name=name, in_out='INPUT', socket_type=kind)
    s.default_value = default
    i = next(n for n in group.nodes if n.type == 'GROUP_INPUT')
    return i.outputs[name]


def instancer_attribute(tree, name, fallback):
    """输入实例属性名与母资产默认值，返回实例属性信号；非实例编辑场景使用明确回退值。"""
    a = node(tree, 'ShaderNodeAttribute', 'instance_parameter')
    a.attribute_type = 'INSTANCER'; a.attribute_name = name
    a['chair_instance_property'] = name
    # Missing attributes return Alpha=0. This keeps the directly edited mother asset readable.
    found = math(tree, 'GREATER_THAN', a.outputs['Alpha'], 0)
    return math(tree, 'ADD', math(tree, 'MULTIPLY', a.outputs['Fac'], found),
        math(tree, 'MULTIPLY', fallback, math(tree, 'SUBTRACT', 1, found)))


def wood_factory(group):
    """输入复制的木材工艺组，增加同通道UV裁切和轻微木色差异；坐标不越界、不旋转法线。"""
    made = set(group.nodes)
    i = next(n for n in group.nodes if n.type == 'GROUP_INPUT')
    o = next(n for n in group.nodes if n.type == 'GROUP_OUTPUT')
    seed = new_input(group, 'Seed Grain', 'NodeSocketInt', 0)
    amount = new_input(group, 'Grain Variation', default=1)
    amount = clamp(group, amount)
    rx, ry = random_signal(group, seed, 1), random_signal(group, seed, 2)
    sx = math(group, 'SUBTRACT', 1, math(group, 'MULTIPLY', amount, math(group, 'ADD', .04, math(group, 'MULTIPLY', rx, .20))))
    sy = math(group, 'SUBTRACT', 1, math(group, 'MULTIPLY', amount, math(group, 'ADD', .03, math(group, 'MULTIPLY', ry, .17))))
    ox = math(group, 'MULTIPLY', math(group, 'SUBTRACT', 1, sx), random_signal(group, seed, 3))
    oy = math(group, 'MULTIPLY', math(group, 'SUBTRACT', 1, sy), random_signal(group, seed, 4))
    uv = vector(group, 'ADD', vector(group, 'MULTIPLY', i.outputs['Vector'], combine(group, [sx, sy, 1])),
        combine(group, [ox, oy, 0]))
    # All five maps use exactly the same crop; tangent normal orientation remains unchanged.
    for n in group.nodes:
        if n.type == 'TEX_IMAGE': group.links.new(uv, n.inputs['Vector'])
    original = o.inputs['Color'].links[0].from_socket
    warmth = centred(group, random_signal(group, seed, 5), .035)
    brightness = centred(group, random_signal(group, seed, 6), .075)
    tint = combine(group, [math(group, 'ADD', 1, math(group, 'MULTIPLY', amount, math(group, 'ADD', brightness, warmth))),
        math(group, 'ADD', 1, math(group, 'MULTIPLY', amount, brightness)),
        math(group, 'ADD', 1, math(group, 'MULTIPLY', amount, math(group, 'SUBTRACT', brightness, warmth)))])
    coloured = vector(group, 'MULTIPLY', original, tint)
    group.links.new(coloured, o.inputs['Color'])
    frame(group, '实例木纹：同通道安全裁切；轻微明暗／暖色差；Variation=0恢复原工艺',
        [n for n in group.nodes if n not in made])
    group['chair_instance_factory'] = 'wood_grain'


def downstream_math(socket, operation):
    """输入起始接口及目标操作，穿过排版Reroute返回目标Math和进入接口；找不到则停止修改。"""
    queue = [socket]; visited = set()
    while queue:
        value = queue.pop(0)
        for link in value.links:
            n = link.to_node
            if n.name in visited: continue
            visited.add(n.name)
            if n.type == 'MATH' and n.operation == operation: return n, link.to_socket
            if n.type == 'REROUTE': queue.append(n.outputs[0])
    raise RuntimeError('损伤包络接口无法定位')


def metal_wear(group):
    """输入金属表现组，用低成本4D域扭曲改变参考损伤位置／形状与概率，避免逐事件随机造成SVM栈溢出。"""
    made = set(group.nodes)
    i = next(n for n in group.nodes if n.type == 'GROUP_INPUT')
    seed = new_input(group, 'Seed Wear', 'NodeSocketInt', 0)
    amount = new_input(group, 'Wear Variation', default=1)
    envelope_node, external_socket = downstream_math(i.outputs['Wear Placement'], 'MAXIMUM')
    original_socket = next(s for s in envelope_node.inputs if s != external_socket)
    amount = clamp(group, amount)
    axes = node(group, 'ShaderNodeSeparateXYZ', 'instance_damage_axes')
    group.links.new(i.outputs['Position'], axes.inputs[0])
    top = math(group, 'GREATER_THAN', axes.outputs['Z'], .75)
    warp = node(group, 'ShaderNodeTexNoise', 'instance_damage_domain')
    warp.noise_dimensions = '4D'; warp.inputs['Scale'].default_value = 8
    warp.inputs['Detail'].default_value = 2
    group.links.new(i.outputs['Position'], warp.inputs['Vector'])
    group.links.new(math(group, 'MULTIPLY', seed, .071), warp.inputs['W'])
    extent = combine(group, [math(group, 'ADD', .006, math(group, 'MULTIPLY', top, .095)),
        .0015, math(group, 'SUBTRACT', .042, math(group, 'MULTIPLY', top, .0405))])
    shift = vector(group, 'MULTIPLY', vector(group, 'SUBTRACT', warp.outputs['Color'], (.5,.5,.5)), extent)
    shift = vector(group, 'MULTIPLY', shift, amount)
    # The broad upper scrape changes its length; body/joint events retain plausible physical contact regions.
    width = math(group, 'ADD', 1, math(group, 'MULTIPLY', math(group, 'MULTIPLY', top, amount),
        centred(group, random_signal(group, seed, 40), .40)))
    warped = vector(group, 'ADD', vector(group, 'MULTIPLY', i.outputs['Position'], combine(group,[width,1,1])), shift)
    envelope = placement(group, warped)
    gate = node(group, 'ShaderNodeTexNoise', 'instance_damage_coverage')
    gate.noise_dimensions = '4D'; gate.inputs['Scale'].default_value = 22; gate.inputs['Detail'].default_value = 2
    group.links.new(warped, gate.inputs['Vector'])
    group.links.new(math(group,'MULTIPLY',seed,.113),gate.inputs['W'])
    interrupted = clamp(group, math(group, 'MULTIPLY', math(group, 'SUBTRACT', gate.outputs['Fac'], .40), 4))
    coverage = math(group,'ADD',.30,math(group,'MULTIPLY',interrupted,1.20))
    coverage = math(group,'ADD',1,math(group,'MULTIPLY',amount,math(group,'SUBTRACT',coverage,1)))
    group.links.new(math(group,'MULTIPLY',envelope,coverage),original_socket)
    # Change high-resolution chip-field phase much more than the old 7.5% sampling shift.
    phase = next(n for n in group.nodes if n.get('chair_metal_role') == 'appearance_seed_phase')
    for s in phase.inputs:
        n = s.links[0].from_node
        assert n.type == 'MATH' and n.operation == 'MULTIPLY'
        n.inputs[1].default_value = .65
    frame(group, '实例磨损：4D域扭曲改变位置／宽度／覆盖；4K破边相位独立变化；Variation=0恢复原位置包络',
        [n for n in group.nodes if n not in made])
    group['chair_instance_wear'] = True


def shared_material(mat, groups, root):
    """输入本椅材质、组缓存与默认控制对象，替换为共享组和Instancer属性；返回共享材质。"""
    mat.name = 'Chair shared / ' + mat['chair_source_material']
    del mat['chair_owner']; mat['chair_shared_material'] = True
    if mat.node_tree.animation_data: mat.node_tree.animation_data_clear()
    tree = mat.node_tree; made = set(tree.nodes)
    for n in list(tree.nodes):
        if n.type != 'GROUP': continue
        kind, offset = layer_kind(n)
        factory = n.get('wood_layers_role') == 'process'
        if kind or factory:
            original = n.node_tree
            if original not in groups:
                g = original.copy(); g.name = original.name + ' / Instances'
                if factory: wood_factory(g)
                if kind == 'metal': metal_wear(g)
                groups[original] = g
            n.node_tree = groups[original]
        if kind:
            prop = PROPERTIES[kind]
            signal = instancer_attribute(tree, prop, int(root[prop]))
            if offset: signal = math(tree, 'ADD', signal, offset)
            tree.links.new(signal, n.inputs['Seed'])
        if kind == 'metal':
            for prop, fallback in [('Seed Wear', int(root['Seed Wear'])), ('Wear Variation', 1)]:
                tree.links.new(instancer_attribute(tree, prop, fallback), n.inputs[prop])
        if factory:
            signal = instancer_attribute(tree, 'Seed Grain', int(root['Seed Grain']))
            if 'back' in n.node_tree.name: signal = math(tree, 'ADD', signal, 17)
            tree.links.new(signal, n.inputs['Seed Grain'])
            tree.links.new(instancer_attribute(tree, 'Grain Variation', 1), n.inputs['Grain Variation'])
    frame(tree, '共用材质：Attribute / Instancer读取当前整椅实例的种子；母资产编辑使用默认回退',
        [n for n in tree.nodes if n not in made])
    return mat


def counts(parts):
    """输入课椅对象集合，返回实际唯一网格／根材质／拓扑数据量，不当作进程RAM测量。"""
    meshes = {o.data for o in parts}; materials = {m for o in parts for m in o.data.materials if m}
    return {'objects': len(parts), 'meshes': len(meshes), 'materials': len(materials),
        'vertices': sum(len(m.vertices) for m in meshes), 'loops': sum(len(m.loops) for m in meshes)}


def author():
    """输入当前正式镜头，输出共享母资产候选和原场景保护快照；不在验证前覆盖正式文件。"""
    assert Path(bpy.data.filepath) == TARGET
    WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene; bpy.context.view_layer.update()
    target_hash = digest_file(TARGET)
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / 'before_instances.blend'), copy=True)
    roots = sorted([o for o in sc.objects if o.get('chair_asset')], key=lambda o: o.name)
    assert len(roots) == 25 and all(len(o.children) == 29 for o in roots)
    children = [o for r in roots for o in r.children]
    protected_names = [o.name for o in bpy.data.objects if o not in children]
    protected_mats = [m.name for m in bpy.data.materials if not m.get('chair_owner')]
    protected_groups = list(bpy.data.node_groups.keys())
    before = protected(protected_names, protected_mats, protected_groups)
    before_counts = counts(children)
    placements = {o.name: [list(r) for r in o.matrix_world] for o in roots}
    prototypes = sorted(roots[0].children, key=lambda o: o['chair_source_part'])
    geometry = {o['chair_source_part']: geometry_digest(o.data) for o in prototypes}
    matrices = {o['chair_source_part']: [list(r) for r in o.matrix_basis] for o in prototypes}
    # Stop rather than silently discard unique model edits when creating a common mother asset.
    assert all(geometry_digest(o.data) == geometry[o['chair_source_part']] for o in children), '各椅已有不同几何，请保留模型变体'
    for index, root in enumerate(roots, 1):
        for prop, value, description in [
            ('Seed Wear', 421+index*79, '金属损伤位置／长宽／覆盖种子'),
            ('Seed Grain', 221+index*131, '木纹工艺裁切与轻微色调种子'),
            ('Wear Variation', 1.0, '金属位置／尺度差异强度；0恢复原位置'),
            ('Grain Variation', 1.0, '木纹工艺差异强度；0恢复原工艺')]:
            root[prop] = value
            root.id_properties_ui(prop).update(min=0, max=2147483000 if 'Seed' in prop else 1,
                description=description)
    collection = bpy.data.collections.new(MASTER)
    edit = bpy.data.scenes.new(EDIT); edit.collection.children.link(collection)
    edit.world = sc.world; edit.unit_settings.system = 'METRIC'
    group_cache = {}; materials = {m for o in prototypes for m in o.data.materials if m}
    for mat in materials: shared_material(mat, group_cache, roots[0])
    expected_parts = []
    for o in prototypes:
        local = o.matrix_basis.copy()
        for c in list(o.users_collection): c.objects.unlink(o)
        collection.objects.link(o)
        o.parent = None; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_world = local
        o.name = 'Chair master / ' + o['chair_source_part']; o['chair_master_part'] = True
        del o['chair_owner']
        expected_parts.append({'name': o.name, 'source': o['chair_source_part'], 'mesh': o.data.name,
            'materials': [m.name for m in o.data.materials], 'matrix': [list(r) for r in local]})
    redundant_meshes = {o.data for o in children if o not in prototypes}
    redundant_mats = {m for o in children if o not in prototypes for m in o.data.materials if m}
    for o in children:
        if o not in prototypes: bpy.data.objects.remove(o, do_unlink=True)
    for mesh in redundant_meshes:
        assert mesh.users == 0; bpy.data.meshes.remove(mesh)
    for mat in redundant_mats:
        assert mat.users == 0; bpy.data.materials.remove(mat)
    for c in list(bpy.data.collections):
        if c.name.startswith('CHAIR ') and c.name.endswith('/ Editable parts'):
            assert len(c.objects) == 0; bpy.data.collections.remove(c)
    for root in roots:
        root.instance_type = 'COLLECTION'; root.instance_collection = collection
        root['chair_asset'] = 'Shared editable collection / instance parameters'
    # The editor scene offers the full 29-part mother asset without adding its geometry a second time to the classroom.
    bpy.context.view_layer.update()
    assert before == protected(protected_names, protected_mats, protected_groups)
    expected = {'protected': before, 'protected_names': protected_names, 'protected_mats': protected_mats,
        'protected_groups': protected_groups, 'placements': placements, 'parts': expected_parts,
        'geometry': geometry, 'matrices': matrices, 'scene': sc.name, 'edit_scene': EDIT,
        'master': MASTER, 'target_before_sha256': target_hash, 'before_counts': before_counts,
        'after_counts': counts(prototypes),
        'parameters': {r.name: {p: r[p] for p in list(PROPERTIES.values()) + ['Seed Wear','Seed Grain','Wear Variation','Grain Variation']} for r in roots},
        'materials': {m.name: scene_signature(m.node_tree) for m in materials},
        'new_groups': {g.name: scene_signature(g) for g in group_cache.values()}}
    dump(OUT / 'expected.json', expected)
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    print('CHAIR_INSTANCE_CANDIDATE', {'before': before_counts, 'after': expected['after_counts']}, flush=True)


def verify(published=False):
    """输入独立重开的候选／正式文件，核验保护、共享引用、实例矩阵与参数，输出检查结果。"""
    expected = json.loads((OUT / 'expected.json').read_text(encoding='utf-8'))
    sc = bpy.data.scenes[expected['scene']]; bpy.context.window.scene = sc
    sc.frame_set(sc.frame_current); bpy.context.view_layer.update()
    checks = {}; current = protected(expected['protected_names'], expected['protected_mats'], expected['protected_groups'])
    for key, value in expected['protected'].items(): checks['preserve/' + key] = current[key] == value
    master = bpy.data.collections[MASTER]
    checks['29_master_parts'] = len(master.objects) == 29
    checks['master_in_editor_only'] = master in list(bpy.data.scenes[EDIT].collection.children) and not any(o in sc.objects[:] for o in master.objects)
    roots = [bpy.data.objects[name] for name in expected['placements']]
    for root in roots:
        checks[root.name + '/instance'] = root.instance_collection == master and root.instance_type == 'COLLECTION' and len(root.children) == 0
        checks[root.name + '/placement'] = [list(r) for r in root.matrix_world] == expected['placements'][root.name]
        checks[root.name + '/parameters'] = all(root[p] == value for p, value in expected['parameters'][root.name].items())
    for part in expected['parts']:
        o = bpy.data.objects[part['name']]
        checks[o.name + '/geometry'] = geometry_digest(o.data) == expected['geometry'][part['source']]
        # Unplaced asset objects have no evaluated world cache in the classroom view layer; use saved local transforms.
        checks[o.name + '/matrix'] = max(abs(o.matrix_basis[a][b]-part['matrix'][a][b]) for a in range(4) for b in range(4)) < 1e-5
        checks[o.name + '/materials'] = [m.name for m in o.data.materials] == part['materials']
    for name, signature in expected['materials'].items(): checks[name + '/graph'] = scene_signature(bpy.data.materials[name].node_tree) == signature
    for name, signature in expected['new_groups'].items(): checks[name + '/graph'] = scene_signature(bpy.data.node_groups[name]) == signature
    # Inspect evaluated instances: all 725 leaf copies must point back to exactly 29 original source meshes.
    # DepsgraphObjectInstance is an ephemeral iterator item. Store datablock references immediately, not the iterator structs.
    evaluated = [(i.object.original.data, i.parent.original.name, i.object.original.name, i.matrix_world.copy()) for i in bpy.context.evaluated_depsgraph_get().object_instances
        if i.is_instance and i.object.original in master.objects[:]]
    checks['725_evaluated_parts'] = len(evaluated) == 725
    checks['29_shared_evaluated_meshes'] = len({item[0] for item in evaluated}) == 29
    part_lookup = {p['name']: Matrix(p['matrix']) for p in expected['parts']}
    checks['evaluated_instance_assembly'] = all(max(abs(matrix[a][b]-(Matrix(expected['placements'][parent])@part_lookup[name])[a][b])
        for a in range(4) for b in range(4)) < 1e-5 for mesh, parent, name, matrix in evaluated)
    checks['31_shared_materials'] = counts(list(master.objects))['materials'] == 31
    checks['25_unique_grain_and_wear_seeds'] = all(len({r[p] for r in roots}) == 25 for p in ['Seed Wear', 'Seed Grain'])
    checks['no_per_chair_material_drivers'] = all(not bpy.data.materials[name].node_tree.animation_data for name in expected['materials'])
    attrs = [n for name in expected['materials'] for n in bpy.data.materials[name].node_tree.nodes
        if n.get('chair_instance_property')]
    checks['instancer_attribute_bindings'] = bool(attrs) and all(n.type == 'ATTRIBUTE' and n.attribute_type == 'INSTANCER'
        and n.attribute_name == n['chair_instance_property'] for n in attrs)
    audit = {'file': bpy.data.filepath, 'passed': all(checks.values()), 'checks': checks,
        'before': expected['before_counts'], 'after': counts(list(master.objects)), 'evaluated_parts': len(evaluated)}
    dump(OUT / ('published_validation.json' if published else 'candidate_validation.json'), audit)
    assert audit['passed'], [k for k,v in checks.items() if not v]
    print('CHAIR_INSTANCES_REOPEN', {k:v for k,v in audit.items() if k != 'checks'}, flush=True)


def publish():
    """输入已验证并实际渲染候选，核对目标哈希后原位保存，输出发布哈希。"""
    e = json.loads((OUT / 'expected.json').read_text(encoding='utf-8'))
    v = json.loads((OUT / 'candidate_validation.json').read_text(encoding='utf-8'))
    assert v['passed'] and Path(bpy.data.filepath) == CANDIDATE
    assert digest_file(TARGET) == e['target_before_sha256'], '正式文件发生新保存，需重新合并'
    assert (OUT / 'variants.png').is_file() and (OUT / 'wear_seed_probe.json').is_file()
    assert json.loads((OUT / 'wear_seed_probe.json').read_text(encoding='utf-8'))['passed']
    assert json.loads((OUT / 'grain_seed_probe.json').read_text(encoding='utf-8'))['passed']
    assert 'ERROR Shader graph' not in (WORK / 'review.log').read_text(encoding='utf-8', errors='replace')
    assert (OUT / 'classroom.png').is_file()
    assert 'ERROR Shader graph' not in (WORK / 'classroom.log').read_text(encoding='utf-8', errors='replace')
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
    dump(OUT / 'published.json', {'file': str(TARGET), 'before_sha256': e['target_before_sha256'],
        'after_sha256': digest_file(TARGET), 'counts': e['after_counts'], 'instances': 25})
    print('CHAIR_INSTANCES_PUBLISHED', flush=True)


def repair_scale():
    """输入已生成候选，修正域扭曲强度接口并更新图签名；保存正确重映射的修改前恢复副本。"""
    bpy.ops.wm.open_mainfile(filepath=str(TARGET))
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / 'before_instances.blend'), copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
    e = json.loads((OUT / 'expected.json').read_text(encoding='utf-8'))
    for name in e['new_groups']:
        g = bpy.data.node_groups[name]
        if g.get('chair_instance_wear'):
            for n in g.nodes:
                if n.type == 'VECT_MATH' and n.operation == 'SCALE' and n.get('chair_metal_role') == 'SCALE':
                    n.operation = 'MULTIPLY'
        e['new_groups'][name] = scene_signature(g)
    dump(OUT / 'expected.json', e)
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    print('CHAIR_INSTANCE_SCALE_REPAIRED', flush=True)


def refine_coverage():
    """输入候选，增强上横管掉漆的断续概率；更新共享图签名，保留其它参数与原场景。"""
    e = json.loads((OUT / 'expected.json').read_text(encoding='utf-8'))
    for name in e['new_groups']:
        g = bpy.data.node_groups[name]
        if g.get('chair_instance_wear'):
            gate = next(n for n in g.nodes if n.get('chair_metal_role') == 'instance_damage_coverage')
            multiply = gate.outputs['Fac'].links[0].to_node
            assert multiply.type == 'MATH' and multiply.operation == 'MULTIPLY'
            addition = multiply.outputs[0].links[0].to_node
            multiply.inputs[1].default_value = 1.20; addition.inputs[0].default_value = .30
            made = set(g.nodes)
            signal = clamp(g, math(g,'MULTIPLY',math(g,'SUBTRACT',gate.outputs['Fac'],.40),4))
            g.links.new(signal,multiply.inputs[0])
            # The new nodes belong to the existing explanatory frame, with native names retained.
            f = next(n for n in g.nodes if n.type == 'FRAME' and n.label.startswith('实例磨损'))
            for n in g.nodes:
                if n not in made: n.parent = f
            e['new_groups'][name] = scene_signature(g)
    dump(OUT / 'expected.json', e)
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    print('CHAIR_COVERAGE_REFINED', flush=True)


if __name__ == '__main__':
    if '--refine-coverage' in sys.argv: refine_coverage()
    elif '--repair-scale' in sys.argv: repair_scale()
    elif '--verify' in sys.argv: verify('--published' in sys.argv)
    elif '--publish' in sys.argv: publish()
    else: author()
