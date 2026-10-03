"""制作椅子金属候选：钢材／漆工艺与资产定向掉漆、锈、老化、划痕、脏渍。

输入实时恢复副本与原生SD4K通道；保留原网格、UV、法线及全部木材。
连续米制三维映射用于材质内容，解析位置包络用于损伤；不重展UV。
"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wood_layers_blender import socket, aim
from tripo_wood_reference_blender import color
from tripo_wood_appearance_blender import process_signature
from cleanup_wood_rear_stamp import geometry_digest

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '07_pipeline/cache/chair_metal_layers_20261001'
OUT = ROOT / '06_review/chair_metal_layers_20261001'
TEX = ROOT / '02_assets/textures/generated/chair_metal_layers'
BASELINE = WORK / 'baseline.blend'
CANDIDATE = WORK / 'chair_metal_layers.blend'
CURRENT = ROOT / '02_assets/work/school_chair.blend'
PARTS = ['LP_part_' + f'{i:02}' for i in [1, 4, 5, 8, 13, 16, 21, 22, 23, 24, 25]]
CONTROLS = {'Wear': 1, 'Rust': .94, 'Age': .72, 'Scratches': .80, 'Dirt': .70}
MAT_NAME = 'Chair metal / Grey-white enamel on steel'
FASTENER_NAME = 'Chair metal / Dark oxidized fasteners'


def node(tree, kind, role):
    """输入节点类型与内部用途，返回保留软件默认名称／标题的新节点。"""
    n = tree.nodes.new(kind)
    n['chair_metal_role'] = role
    return n


def bind(tree, source, target):
    """输入常数或节点接口与目标接口，写默认值或连接，返回目标接口。"""
    if hasattr(source, 'node'):
        tree.links.new(source, target)
    else:
        target.default_value = source
    return target


def math(tree, operation, a, b=0):
    """输入标量运算及两个值，返回输出接口；常数与信号均可。"""
    n = node(tree, 'ShaderNodeMath', operation)
    n.operation = operation
    bind(tree, a, n.inputs[0]); bind(tree, b, n.inputs[1])
    return n.outputs[0]


def vector(tree, operation, a, b):
    """输入向量运算与两值，返回向量接口，用于米制映射。"""
    n = node(tree, 'ShaderNodeVectorMath', operation)
    n.operation = operation
    bind(tree, a, n.inputs[0]); bind(tree, b, n.inputs[1])
    return n.outputs['Vector']


def blend(tree, base, foreground, amount, role):
    """输入颜色／灰度值和混合蒙版，返回线性混合接口。"""
    n = node(tree, 'ShaderNodeMixRGB', role)
    n.blend_type = 'MIX'
    bind(tree, amount, n.inputs[0])
    for value, target in [(base, n.inputs[1]), (foreground, n.inputs[2])]:
        if isinstance(value, (int, float)):
            value = (value, value, value, 1)
        bind(tree, value, target)
    return n.outputs['Color']


def clamp(tree, value):
    """输入标量，返回限制到0–1的接口。"""
    return math(tree, 'MINIMUM', math(tree, 'MAXIMUM', value, 0), 1)


def noise(tree, position, scale, detail=3):
    """输入连续米制位置和每米频率，返回3D噪声；避免UV接缝。"""
    n = node(tree, 'ShaderNodeTexNoise', 'physical_noise')
    n.noise_dimensions = '3D'
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = .7
    tree.links.new(position, n.inputs['Vector'])
    return n.outputs['Fac']


def image(tree, name, coords):
    """输入SD通道与世界坐标，返回显式三向混合，避免对象旋转使BOX坐标／法线错位。"""
    projections = [next((n for n in tree.nodes if n.get('chair_metal_role') == 'projection_' + axis), None)
        for axis in 'xyz']
    if projections[0] is None:
        sep = node(tree, 'ShaderNodeSeparateXYZ', 'projection_coordinates')
        tree.links.new(coords, sep.inputs[0])
        geo = node(tree, 'ShaderNodeNewGeometry', 'projection_world_normal')
        normal = node(tree, 'ShaderNodeSeparateXYZ', 'projection_normal_axes')
        # 用对象法线恢复原始装配朝向，移动／旋转部件时纹理仍锁在表面。
        local = node(tree, 'ShaderNodeVectorTransform', 'projection_object_normal')
        local.vector_type = 'NORMAL'; local.convert_from = 'WORLD'; local.convert_to = 'OBJECT'
        tree.links.new(geo.outputs['Normal'], local.inputs[0])
        rotation = node(tree, 'ShaderNodeVectorRotate', 'projection_bind_normal')
        rotation.rotation_type = 'EULER_XYZ'; rotation.inputs['Rotation'].default_value = (1.57079632679, 0, 0)
        tree.links.new(local.outputs[0], rotation.inputs['Vector'])
        tree.links.new(rotation.outputs[0], normal.inputs[0])
        weights = [math(tree, 'POWER', math(tree, 'ABSOLUTE', normal.outputs[a]), 6) for a in 'XYZ']
        xy = math(tree, 'ADD', weights[0], weights[1])
        ratios = [math(tree, 'DIVIDE', weights[1], xy),
            math(tree, 'DIVIDE', weights[2], math(tree, 'ADD', xy, weights[2]))]
        for signal, role in zip(ratios, ['projection_y_ratio', 'projection_z_ratio']):
            signal.node['chair_metal_role'] = role
        projections = []
        for axis, axes in zip('xyz', [('Y', 'Z'), ('X', 'Z'), ('X', 'Y')]):
            p = node(tree, 'ShaderNodeCombineXYZ', 'projection_' + axis)
            tree.links.new(sep.outputs[axes[0]], p.inputs['X'])
            tree.links.new(sep.outputs[axes[1]], p.inputs['Y'])
            projections.append(p)
    ratios = [next(n for n in tree.nodes if n.get('chair_metal_role') == 'projection_' + axis + '_ratio').outputs[0]
        for axis in 'yz']
    im = bpy.data.images.load(str(TEX / (name + '.png')), check_existing=True)
    im.colorspace_settings.name = 'sRGB' if 'Color' in name else 'Non-Color'
    im.pack()
    samples = []
    for axis, p in zip('xyz', projections):
        n = node(tree, 'ShaderNodeTexImage', name + '/' + axis)
        n.image = im; n.projection = 'FLAT'; n.extension = 'REPEAT'; n.interpolation = 'Linear'
        tree.links.new(p.outputs[0], n.inputs['Vector'])
        samples.append(n.outputs['Color'])
    return blend(tree, blend(tree, samples[0], samples[1], ratios[0], name + '/xy'),
        samples[2], ratios[1], name + '/xyz')


def bump(tree, height, normal, distance, role):
    """输入高度、上一层法线及米制标尺，返回只改变着色的法线。"""
    n = node(tree, 'ShaderNodeBump', role)
    n.inputs['Distance'].default_value = distance
    n.inputs['Strength'].default_value = 1
    tree.links.new(height, n.inputs['Height'])
    if normal is not None:
        tree.links.new(normal, n.inputs['Normal'])
    return n.outputs['Normal']


def arrange(tree, label):
    """输入节点树与说明，按依赖深度排版并创建说明框，保留默认节点标题。"""
    depth = {}; rows = {}
    for _ in range(len(tree.nodes)):
        for n in tree.nodes:
            parents = [l.from_node.name for l in tree.links if l.to_node == n]
            if all(p in depth for p in parents):
                depth[n.name] = max([depth[p] for p in parents] or [0]) + 1
    for n in tree.nodes:
        d = depth.get(n.name, 0); row = rows.get(d, 0); rows[d] = row + 1
        n.location = (d * 250, -row * 240)
    f = node(tree, 'NodeFrame', 'comment'); f.label = label
    f.use_custom_color = True; f.color = (.18, .22, .25)
    for n in list(tree.nodes):
        if n != f and n.type not in {'GROUP_INPUT', 'GROUP_OUTPUT', 'OUTPUT_MATERIAL'}:
            xy = n.location.copy(); n.parent = f; n.location = xy


def ellipsoid(tree, position, centre, radii):
    """输入世界位置、损伤中心和三轴米制半径，返回局部接触包络。"""
    p = vector(tree, 'DIVIDE', vector(tree, 'SUBTRACT', position, centre), radii)
    length = node(tree, 'ShaderNodeVectorMath', 'contact_distance')
    length.operation = 'LENGTH'; tree.links.new(p, length.inputs[0])
    return clamp(tree, math(tree, 'SUBTRACT', 1, length.outputs['Value']))


def placement(tree, position):
    """输入连续世界位置，返回参考所示长条掉漆、磕碰及连接锈蚀的位置场。"""
    events = [
        ((-.015, .207, .7928), (.205, .007, .0042), 1.30),
        ((.052, .212, .7835), (.12, .005, .0038), 1.10),
        ((-.155, .207, .759), (.016, .020, .012), .85),
        ((.168, .202, .737), (.020, .020, .009), .70),
        ((-.190, -.201, .071), (.015, .022, .014), 1.23),
        ((.187, -.194, .116), (.013, .026, .018), 1.05),
        ((-.182, -.016, .177), (.018, .023, .016), 1.16),
        ((.181, -.012, .186), (.019, .019, .015), .95),
        ((-.180, .143, .174), (.017, .024, .015), 1.15),
        ((.187, .156, .031), (.014, .022, .011), 1.20),
        ((-.173, .152, .303), (.017, .015, .009), .83),
        ((-.119, -.008, .197), (.025, .016, .008), .78),
        ((.062, -.008, .197), (.023, .015, .009), .88),
        ((-.145, .211, .732), (.021, .012, .014), .80),
        ((.143, .209, .624), (.021, .015, .012), .80),
    ]
    envelope = .16
    for centre, radii, intensity in events:
        event = math(tree, 'MULTIPLY', ellipsoid(tree, position, centre, radii), intensity)
        envelope = math(tree, 'MAXIMUM', envelope, event)
    return envelope


def process_group():
    """返回灰白涂漆工艺组，输出五通道；钢材基底单独输出供露底层调用。"""
    g = bpy.data.node_groups.new('Chair metal / 工艺层 / 钢基底与灰白涂漆', 'ShaderNodeTree')
    socket(g, 'Vector', 'NodeSocketVector')
    for name, kind in [('Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'),
        ('Metallic', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'), ('AO', 'NodeSocketFloat'),
        ('Steel Color', 'NodeSocketColor'), ('Steel Roughness', 'NodeSocketFloat')]:
        socket(g, name, kind, 'OUTPUT')
    i = node(g, 'NodeGroupInput', 'input'); o = node(g, 'NodeGroupOutput', 'output')
    signals = {name: image(g, 'Process_' + name, i.outputs['Vector'])
        for name in ['BaseColor', 'Roughness', 'Metallic', 'Height', 'AO']}
    normal = bump(g, signals['Height'], None, .000045, 'enamel_microrelief')
    for name, signal in [('Color', signals['BaseColor']), ('Roughness', signals['Roughness']),
        ('Metallic', signals['Metallic']), ('Normal', normal), ('AO', signals['AO'])]:
        g.links.new(signal, o.inputs[name])
    o.inputs['Steel Color'].default_value = color((.52, .54, .55))
    o.inputs['Steel Roughness'].default_value = .42
    arrange(g, '工艺层：钢基底／灰白涂漆；漆Metallic=0；米制高度转法线，避免三向映射误用切线法线')
    g['content_tile_m'] = .12
    return g


def appearance_group():
    """返回多通道表现组：定向剥漆、氧化露底、锈蚀、雾化与独立划痕／脏渍。"""
    g = bpy.data.node_groups.new('Chair metal / 表现层 / 掉漆锈蚀老化划痕脏渍', 'ShaderNodeTree')
    for name, kind in [('Vector', 'NodeSocketVector'), ('Position', 'NodeSocketVector'),
        ('Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'),
        ('Normal', 'NodeSocketVector'), ('AO', 'NodeSocketFloat'), ('Steel Color', 'NodeSocketColor'),
        ('Steel Roughness', 'NodeSocketFloat')]:
        socket(g, name, kind)
    for k, v in CONTROLS.items():
        socket(g, k, 'NodeSocketFloat', default=v)
    socket(g, 'Wear Placement', 'NodeSocketFloat', default=0)
    for name, kind in [('Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'),
        ('Metallic', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'), ('AO', 'NodeSocketFloat'),
        ('Coat', 'NodeSocketFloat'), ('Coat Roughness', 'NodeSocketFloat'),
        ('Chip Mask', 'NodeSocketFloat'), ('Rust Mask', 'NodeSocketFloat')]:
        socket(g, name, kind, 'OUTPUT')
    i = node(g, 'NodeGroupInput', 'input'); o = node(g, 'NodeGroupOutput', 'output')
    t = {k: image(g, k, i.outputs['Vector']) for k in
        ['ChipField', 'RustColor', 'RustRoughness', 'RustHeight', 'AgeMask', 'ScratchMask', 'DirtMask']}
    axes = node(g, 'ShaderNodeSeparateXYZ', 'oxide_position')
    g.links.new(i.outputs['Position'], axes.inputs[0])
    top = math(g, 'GREATER_THAN', axes.outputs['Z'], .75)
    # 上横管以深褐氧化印为主，脚部保留赭色锈，与用户照片的两类旧化一致。
    rust_color = blend(g, t['RustColor'], color((.115, .098, .076)),
        math(g, 'MULTIPLY', top, .72), 'aged_dark_upper_oxide')
    envelope = placement(g, i.outputs['Position'])
    envelope = math(g, 'MAXIMUM', envelope, i.outputs['Wear Placement'])
    field = math(g, 'ADD', t['ChipField'], math(g, 'MULTIPLY', envelope, .75))
    chip = clamp(g, math(g, 'MULTIPLY', math(g, 'SUBTRACT', field, .91), 32))
    chip = math(g, 'MULTIPLY', chip, i.outputs['Wear'])
    corrosion = noise(g, i.outputs['Position'], 310, 4)
    # 漆口保留部分钢灰；氧化与掉漆位置一致，锈不是金属。
    oxide = clamp(g, math(g, 'MULTIPLY', math(g, 'SUBTRACT', corrosion, .34), 5.5))
    rust = math(g, 'MULTIPLY', math(g, 'MULTIPLY', chip, oxide), i.outputs['Rust'])
    age = math(g, 'MULTIPLY', t['AgeMask'], i.outputs['Age'])
    scratches = math(g, 'MULTIPLY', t['ScratchMask'], i.outputs['Scratches'])
    intact = math(g, 'SUBTRACT', 1, chip)
    scratches = math(g, 'MULTIPLY', scratches, intact)
    dirt = math(g, 'MULTIPLY', t['DirtMask'], math(g, 'MULTIPLY', i.outputs['Dirt'], .65))
    aged = blend(g, i.outputs['Color'], color((.565, .585, .523)), math(g, 'MULTIPLY', age, .40), 'paint_oxidation_colour')
    steel = blend(g, i.outputs['Steel Color'], color((.115, .127, .120)), math(g, 'MULTIPLY', corrosion, .90), 'oxidized_exposed_steel')
    colour = blend(g, aged, steel, chip, 'lost_paint_exposes_steel')
    colour = blend(g, colour, rust_color, rust, 'oxide_microcolour')
    colour = blend(g, colour, color((.28, .29, .265)), math(g, 'MULTIPLY', scratches, .44), 'scratch_scuff_colour')
    colour = blend(g, colour, color((.19, .177, .142)), dirt, 'dry_residue_colour')
    rough = blend(g, i.outputs['Roughness'], .52, age, 'paint_haze_roughness')
    rough = blend(g, rough, i.outputs['Steel Roughness'], chip, 'bare_steel_roughness')
    rough = blend(g, rough, t['RustRoughness'], rust, 'porous_oxide_roughness')
    rough = blend(g, rough, .57, scratches, 'scuff_roughness')
    rough = blend(g, rough, .79, dirt, 'dry_dirt_roughness')
    # Rust=0时露出底钢；锈层覆盖改变金属性，漆口仍保留少量钢灰。
    metal = blend(g, i.outputs['Metallic'], math(g, 'SUBTRACT', 1,
        math(g, 'MULTIPLY', oxide, i.outputs['Rust'])), chip, 'metal_exposure')
    metal = math(g, 'MULTIPLY', metal, math(g, 'SUBTRACT', 1, dirt))
    cut = math(g, 'MULTIPLY', chip, -.90)
    normal = bump(g, cut, i.outputs['Normal'], .000075, 'paint_edge_step')
    rh = math(g, 'MULTIPLY', math(g, 'SUBTRACT', t['RustHeight'], .5), rust)
    normal = bump(g, rh, normal, .000120, 'oxide_pitting')
    sh = math(g, 'MULTIPLY', scratches, -1)
    normal = bump(g, sh, normal, .000020, 'shallow_scuffs')
    normal = bump(g, dirt, normal, .000016, 'deposited_residue')
    coat = math(g, 'MULTIPLY', .075, intact)
    coat = math(g, 'MULTIPLY', coat, math(g, 'SUBTRACT', 1, dirt))
    coat_r = blend(g, .32, .49, age, 'coat_haze')
    for name, signal in [('Color', colour), ('Roughness', rough), ('Metallic', metal),
        ('Normal', normal), ('AO', i.outputs['AO']), ('Coat', coat), ('Coat Roughness', coat_r),
        ('Chip Mask', chip), ('Rust Mask', rust)]:
        g.links.new(signal, o.inputs[name])
    arrange(g, '表现层：参考位置×4K破边；掉漆约75µm，锈微孔≤120µm；五个强度归零恢复工艺')
    g['reference_events'] = 'Upper front rail long scrape; joints, tube feet, isolated impacts'
    return g


def material():
    """创建独立金属材质及两个主分层节点，返回材质与表现控制节点。"""
    mat = bpy.data.materials.new(MAT_NAME); mat.use_nodes = True
    tree = mat.node_tree
    shader = tree.nodes.get('Principled BSDF'); output = tree.nodes.get('Material Output')
    geo = node(tree, 'ShaderNodeNewGeometry', 'physical_position')
    coords = vector(tree, 'MULTIPLY', geo.outputs['Position'], (1 / .12,) * 3)
    proc = node(tree, 'ShaderNodeGroup', 'process'); proc.node_tree = process_group()
    app = node(tree, 'ShaderNodeGroup', 'appearance'); app.node_tree = appearance_group()
    for g in [proc, app]:
        tree.links.new(coords, g.inputs['Vector'])
    tree.links.new(geo.outputs['Position'], app.inputs['Position'])
    for channel in ['Color', 'Roughness', 'Metallic', 'Normal', 'AO', 'Steel Color', 'Steel Roughness']:
        tree.links.new(proc.outputs[channel], app.inputs[channel])
    for a, b in [('Color', 'Base Color'), ('Roughness', 'Roughness'), ('Metallic', 'Metallic'),
        ('Normal', 'Normal'), ('Coat', 'Coat Weight'), ('Coat Roughness', 'Coat Roughness'), ('Normal', 'Coat Normal')]:
        tree.links.new(app.outputs[a], shader.inputs[b])
    tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    arrange(tree, '金属材质：工艺层→表现层→Principled BSDF；12cm米制内容，原UV／法线保留')
    proc.location = (-450, 250); app.location = (-100, 250); shader.location = (280, 250)
    output.location = (750, 250)
    mat['chair_metal_layers'] = True
    return mat, app


def fastener_material(source):
    """输入灰白漆分层材质，返回独立深色氧化螺钉变体；不把螺钉刷成白漆。"""
    mat = source.copy(); mat.name = FASTENER_NAME
    proc = next(n for n in mat.node_tree.nodes if n.get('chair_metal_role') == 'process')
    app = next(n for n in mat.node_tree.nodes if n.get('chair_metal_role') == 'appearance')
    proc.node_tree = proc.node_tree.copy()
    proc.node_tree.name = 'Chair metal / 工艺层 / 深色氧化螺钉'
    out = next(n for n in proc.node_tree.nodes if n.type == 'GROUP_OUTPUT')
    base = out.inputs['Color'].links[0].from_socket
    tint = node(proc.node_tree, 'ShaderNodeMixRGB', 'dark_oxide_finish')
    tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (.04, .045, .048, 1)
    proc.node_tree.links.new(base, tint.inputs[1])
    proc.node_tree.links.new(tint.outputs['Color'], out.inputs['Color'])
    for l in list(out.inputs['Metallic'].links):
        proc.node_tree.links.remove(l)
    out.inputs['Metallic'].default_value = .75
    app.inputs['Wear'].default_value = .8; app.inputs['Rust'].default_value = .55
    app.inputs['Age'].default_value = .05; app.inputs['Dirt'].default_value = .65
    app.inputs['Wear Placement'].default_value = .65
    arrange(proc.node_tree, '工艺层：深色氧化紧固件；独立色调与金属性，保持灰白漆管架')
    return mat, app


def bind_material(template, ob):
    """输入分层模板与原部件，返回锁定本地坐标的材质；移动部件不会滑动旧化。"""
    mat = template.copy()
    mat.name = 'Chair metal / ' + ('Fastener / ' if template.name == FASTENER_NAME else 'Paint / ') + ob.name
    tree = mat.node_tree
    geo = next(n for n in tree.nodes if n.get('chair_metal_role') == 'physical_position')
    tex = node(tree, 'ShaderNodeTexCoord', 'bound_object_coordinate')
    scaled = vector(tree, 'MULTIPLY', tex.outputs['Object'], tuple(ob.scale))
    rot = node(tree, 'ShaderNodeVectorRotate', 'original_assembly_rotation')
    rot.rotation_type = 'EULER_XYZ'; rot.inputs['Rotation'].default_value = tuple(ob.rotation_euler)
    tree.links.new(scaled, rot.inputs['Vector'])
    bound = vector(tree, 'ADD', rot.outputs[0], tuple(ob.location))
    for link in list(geo.outputs['Position'].links):
        tree.links.new(bound, link.to_socket)
    tree.nodes.remove(geo)
    mat['bound_part'] = ob.name
    mat['coordinate_method'] = 'Object local position restored to original assembly metres; no UV stretch'
    # 全部Tripo部件原始旋转相同，法线投射与绑定朝向匹配。
    assert abs(ob.rotation_euler.x - 1.57079632679) < 1e-5
    assert abs(ob.rotation_euler.y) < 1e-5 and abs(ob.rotation_euler.z) < 1e-5
    app = next(n for n in tree.nodes if n.get('chair_metal_role') == 'appearance')
    return mat, app


def protected():
    """读取当前椅子，返回全部原几何／UV／法线与木材／胶脚／旧金属材质摘要。"""
    data = {'geometry': {}, 'materials': {}, 'transforms': {}}
    for ob in bpy.data.objects:
        data['transforms'][ob.name] = [list(row) for row in ob.matrix_world]
        if ob.type == 'MESH':
            data['geometry'][ob.name] = geometry_digest(ob.data)
    for mat in bpy.data.materials:
        if mat.use_nodes and not mat.get('chair_metal_layers'):
            data['materials'][mat.name] = process_signature(mat.node_tree)
    for group in bpy.data.node_groups:
        if not group.name.startswith('Chair metal /'):
            data['materials'][group.name] = process_signature(group)
    return data


def render(name, view, width=1500, height=1100):
    """输入评审标签和透视机位，输出固定三点布光／种子PNG，不保存机位变化。"""
    if '--fast' in sys.argv:
        return
    sc = bpy.context.scene
    sc.camera.location = view[0]; sc.camera.data.lens = view[2]
    aim(sc.camera, view[1])
    sc.render.resolution_x = width; sc.render.resolution_y = height; sc.render.resolution_percentage = 100
    sc.render.filepath = str(OUT / (name + '.png'))
    bpy.ops.render.render(write_still=True)
    print('CHAIR_METAL_RENDER ' + name, flush=True)


def run():
    """从恢复副本制作分层候选、渲染同光对照，保护检查后保存，返回审计。"""
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    before = protected()
    scene_state = {'location': list(sc.camera.location), 'rotation': list(sc.camera.rotation_euler),
        'lens': sc.camera.data.lens, 'resolution': [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
        'filepath': sc.render.filepath, 'samples': sc.cycles.samples, 'seed': sc.cycles.seed,
        'depth': sc.render.image_settings.color_depth, 'device': sc.cycles.device}
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    sc.cycles.device = 'GPU'; sc.cycles.samples = 64; sc.cycles.seed = 101
    sc.cycles.use_animated_seed = False; sc.render.image_settings.color_depth = '8'
    whole = ((.98, -1.3, .99), (0, 0, .42), 55)
    rail = ((.25, -.42, .87), (0, .214, .789), 105)
    foot = ((.12, -.48, .24), (-.175, -.125, .14), 95)
    rear = ((.47, .86, .77), (0, .16, .55), 68)
    render('00_before_whole', whole)
    mat, app = material()
    pairs = []
    for name in PARTS:
        ob = bpy.data.objects[name]
        bound, control = bind_material(mat, ob)
        ob.data.materials[0] = bound
        pairs.append((bound, control))
    heads = [o for o in bpy.data.objects if o.type == 'MESH' and
        any(m and m.name == 'AITA dark fastener heads' for m in o.data.materials)]
    fastener, head_app = fastener_material(mat)
    for ob in heads:
        bound, control = bind_material(fastener, ob)
        ob.data.materials[0] = bound
        pairs.append((bound, control))
    settings = {m.name: {k: a.inputs[k].default_value for k in CONTROLS} for m, a in pairs}
    render('01_after_whole', whole)
    render('02_after_rail', rail, 1800, 1000)
    render('03_after_foot', foot, 1600, 1200)
    render('04_after_rear', rear)
    for m, a in pairs:
        for k in CONTROLS:
            a.inputs[k].default_value = 0
    render('05_process_rail', rail, 1800, 1000)
    render('06_process_whole', whole)
    # 直接接工艺输出作独立对照，检验表现归零不是仅数值变成0。
    for m, a in pairs:
        shader = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        proc = next(n for n in m.node_tree.nodes if n.get('chair_metal_role') == 'process')
        for source, target in [('Color', 'Base Color'), ('Roughness', 'Roughness'), ('Metallic', 'Metallic'), ('Normal', 'Normal'), ('Normal', 'Coat Normal')]:
            m.node_tree.links.new(proc.outputs[source], shader.inputs[target])
        for name, value in [('Coat Weight', .075), ('Coat Roughness', .32)]:
            for link in list(shader.inputs[name].links):
                m.node_tree.links.remove(link)
            shader.inputs[name].default_value = value
    render('07_direct_process_whole', whole)
    for m, a in pairs:
        shader = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for source, target in [('Color', 'Base Color'), ('Roughness', 'Roughness'), ('Metallic', 'Metallic'), ('Normal', 'Normal'),
            ('Coat', 'Coat Weight'), ('Coat Roughness', 'Coat Roughness'), ('Normal', 'Coat Normal')]:
            m.node_tree.links.new(a.outputs[source], shader.inputs[target])
        for k, value in settings[m.name].items():
            a.inputs[k].default_value = value
    sc.camera.location = scene_state['location']; sc.camera.rotation_euler = scene_state['rotation']
    sc.camera.data.lens = scene_state['lens']
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = scene_state['resolution']
    sc.render.filepath = scene_state['filepath']; sc.cycles.samples = scene_state['samples']
    sc.cycles.seed = scene_state['seed']; sc.render.image_settings.color_depth = scene_state['depth']
    sc.cycles.device = scene_state['device']
    bpy.context.view_layer.update()
    after = protected()
    if before != after:
        delta = {section: {key: [before[section].get(key), after[section].get(key)]
            for key in set(before[section]) | set(after[section])
            if before[section].get(key) != after[section].get(key)} for section in before}
        (OUT / 'protection_difference.json').write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding='utf-8')
        raise RuntimeError('原模型／木材／旧材质保护检查失败：见protection_difference.json')
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    audit = {'candidate': str(CANDIDATE), 'parts': PARTS, 'controls': CONTROLS,
        'fastener_parts': [o.name for o in heads], 'material_controls': settings,
        'texture_resolution': 4096, 'content_tile_m': .12, 'original_protected': before,
        'protected_unchanged': True, 'baseline_sha256': hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        'saved_candidate_sha256': hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), 'visual_status': 'Pending human visual review'}
    (OUT / 'validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit


if __name__ == '__main__':
    print('CHAIR_METAL_COMPLETE ' + json.dumps({k: v for k, v in run().items() if k != 'original_protected'}, ensure_ascii=False), flush=True)
