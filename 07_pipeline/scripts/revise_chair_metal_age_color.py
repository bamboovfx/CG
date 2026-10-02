"""将课椅漆面老化改为整体灰褐色；保留工艺、损伤、木材与用户场景编辑。"""
from pathlib import Path
import json
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chair_metal_blender import protected, PARTS
from tripo_wood_reference_blender import color
from tripo_wood_appearance_blender import process_signature
from wood_layers_blender import socket, aim

OUT = ROOT / '06_review/chair_metal_age_color_20261001'
WORK = ROOT / '07_pipeline/cache/chair_metal_age_color_20261001'
GROUP = 'Chair metal / 表现层 / 掉漆锈蚀老化划痕脏渍'


def revise():
    """输入当前分层材质，输出调色记录；只改老化颜色路径及11件漆面的Age值。"""
    g = bpy.data.node_groups[GROUP]
    assert not g.get('whole_surface_age_color'), '此组已调色，避免重复插入'
    before = protected()
    process_before = {x.name: process_signature(x) for x in bpy.data.node_groups
                      if x.name.startswith('Chair metal / 工艺层 /')}
    local = next(n for n in g.nodes if n.get('chair_metal_role') == 'paint_oxidation_colour')
    factor = local.inputs[0].links[0].from_node
    assert factor.operation == 'MULTIPLY'
    inp = next(n for n in g.nodes if n.type == 'GROUP_INPUT')
    # 公共覆盖和空间变化都由Age驱动，Age=0时仍严格恢复干净工艺颜色。
    socket(g, 'Age Color', 'NodeSocketColor', default=color((121/255, 105/255, 87/255)))
    socket(g, 'Age Coverage', 'NodeSocketFloat', default=.78)
    socket(g, 'Age Variation', 'NodeSocketFloat', default=.30)
    frame = g.nodes.new('NodeFrame')
    frame.label = '整面老化：灰褐底色＋原4K局部变化；Age=0恢复工艺'
    frame.location = (factor.location.x - 220, factor.location.y + 340)
    global_age = g.nodes.new('ShaderNodeMath')
    global_age.operation = 'MULTIPLY'
    global_age['chair_metal_role'] = 'whole_surface_age_coverage'
    global_age.parent = frame
    global_age.location = (0, 0)
    g.links.new(inp.outputs['Age'], global_age.inputs[0])
    g.links.new(inp.outputs['Age Coverage'], global_age.inputs[1])
    g.links.new(inp.outputs['Age Variation'], factor.inputs[1])
    total = g.nodes.new('ShaderNodeMath')
    total.operation = 'ADD'
    total.use_clamp = True
    total['chair_metal_role'] = 'whole_surface_age_factor'
    total.parent = frame
    total.location = (200, 0)
    g.links.new(global_age.outputs[0], total.inputs[0])
    g.links.new(factor.outputs[0], total.inputs[1])
    g.links.new(total.outputs[0], local.inputs[0])
    g.links.new(inp.outputs['Age Color'], local.inputs[2])
    updated = []
    for name in PARTS:
        mat = bpy.data.objects[name].active_material
        app = next(n for n in mat.node_tree.nodes if n.get('chair_metal_role') == 'appearance')
        app.inputs['Age'].default_value = .95
        app.inputs['Age Color'].default_value = color((121/255, 105/255, 87/255))
        app.inputs['Age Coverage'].default_value = .78
        app.inputs['Age Variation'].default_value = .30
        updated.append(name)
    g['whole_surface_age_color'] = '2026-10-01 #796957 / coverage .78 / variation .30'
    bpy.context.view_layer.update()
    assert protected() == before, '受保护几何、木材或场景发生变化'
    assert process_before == {x.name: process_signature(x) for x in bpy.data.node_groups
                              if x.name.startswith('Chair metal / 工艺层 /')}
    return {'parts': updated, 'age': .95, 'age_color_srgb_hex': '#796957',
            'age_coverage': .78, 'age_variation': .30, 'protected_unchanged': True,
            'process_groups_unchanged': True, 'age_zero_factor': 0.0}


def render_view(file, view, width, height):
    """输入同光透视机位和尺寸，输出真实Cycles评审图；不改变灯光与色彩管理。"""
    sc = bpy.context.scene
    sc.camera.location = view[0]
    aim(sc.camera, view[1])
    sc.camera.data.lens = view[2]
    sc.render.resolution_x = width
    sc.render.resolution_y = height
    sc.render.resolution_percentage = 100
    sc.render.filepath = str(OUT / file)
    bpy.ops.render.render(write_still=True)


def candidate():
    """从实时恢复副本验证调色，保存候选与同光前后图，恢复相机及渲染设置。"""
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    cam = sc.camera
    state = (cam.location.copy(), cam.rotation_euler.copy(), cam.data.lens,
             sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage,
             sc.render.filepath, sc.cycles.samples, sc.cycles.seed, sc.cycles.device,
             sc.render.image_settings.color_depth, sc.cycles.use_animated_seed)
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = 64
    sc.cycles.seed = 101
    sc.cycles.use_animated_seed = False
    sc.render.image_settings.color_depth = '8'
    whole = ((.98, -1.3, .99), (0, 0, .42), 55)
    render_view('before_whole.png', whole, 1280, 940)
    audit = revise()
    render_view('after_whole.png', whole, 1280, 940)
    render_view('after_rail.png', ((.25, -.42, .87), (0, .214, .789), 105), 1400, 780)
    (cam.location, cam.rotation_euler, cam.data.lens,
     sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage,
     sc.render.filepath, sc.cycles.samples, sc.cycles.seed, sc.cycles.device,
     sc.render.image_settings.color_depth, sc.cycles.use_animated_seed) = state
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / 'age_color_candidate.blend'))
    (OUT / 'candidate.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print('AGE_COLOR_CANDIDATE ' + json.dumps(audit), flush=True)


if __name__ == '__main__':
    candidate()
