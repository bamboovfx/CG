"""依据旧课椅参考收回整面褐色，仅校正现有表现层参数，保留其它编辑。"""
from pathlib import Path
import json
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import revise_chair_metal_age_color as original
from chair_metal_blender import protected, PARTS
from tripo_wood_reference_blender import color
from tripo_wood_appearance_blender import process_signature

OUT = ROOT / '06_review/chair_metal_reference_color_20261001'
WORK = original.WORK
VALUES = {'Age': .80, 'Age Coverage': .30, 'Age Variation': .40}
TINT = (150/255, 152/255, 143/255)


def calibrate():
    """输入实时材质，返回11件灰白旧漆参数校正记录；不新增节点或改局部锈蚀。"""
    before = protected()
    groups_before = {g.name: process_signature(g) for g in bpy.data.node_groups
                     if g.name.startswith('Chair metal / 工艺层 /')}
    records = []
    for name in PARTS:
        mat = bpy.data.objects[name].active_material
        app = next(n for n in mat.node_tree.nodes if n.get('chair_metal_role') == 'appearance')
        old = {k: app.inputs[k].default_value for k in VALUES}
        for key, value in VALUES.items():
            app.inputs[key].default_value = value
        app.inputs['Age Color'].default_value = color(TINT)
        records.append({'part': name, 'before': old, 'after': VALUES})
    bpy.context.view_layer.update()
    assert before == protected(), '非金属材质、几何、UV或场景变换被更改'
    assert groups_before == {g.name: process_signature(g) for g in bpy.data.node_groups
                             if g.name.startswith('Chair metal / 工艺层 /')}
    return {'parts': records, 'age_color_srgb_hex': '#96988F', 'protected_unchanged': True,
            'process_groups_unchanged': True, 'local_damage_nodes_unchanged': True}


def candidate():
    """输入当前工程恢复副本，输出同光整椅／横管图及参数校正候选，恢复原机位设置。"""
    OUT.mkdir(parents=True, exist_ok=True)
    original.OUT = OUT
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
    audit = calibrate()
    original.render_view('whole.png', ((.98, -1.3, .99), (0, 0, .42), 55), 1280, 940)
    original.render_view('rail.png', ((.25, -.42, .87), (0, .214, .789), 105), 1400, 780)
    (cam.location, cam.rotation_euler, cam.data.lens,
     sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage,
     sc.render.filepath, sc.cycles.samples, sc.cycles.seed, sc.cycles.device,
     sc.render.image_settings.color_depth, sc.cycles.use_animated_seed) = state
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'reference_color_candidate.blend'))
    (OUT/'candidate.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print('REFERENCE_COLOR_CANDIDATE ' + json.dumps(audit), flush=True)


def verify():
    """输入磁盘重开的结果，复核既有54项检查及当前11件参数，不编辑工程。"""
    import verify_chair_metal
    verify_chair_metal.main()
    checks = {}
    for name in PARTS:
        app = next(n for n in bpy.data.objects[name].active_material.node_tree.nodes
                   if n.get('chair_metal_role') == 'appearance')
        checks[name] = all(abs(app.inputs[k].default_value-v) < 1e-6 for k, v in VALUES.items())
        checks[name] = checks[name] and all(abs(a-b) < 1e-6 for a, b in
                                           zip(app.inputs['Age Color'].default_value, color(TINT)))
    audit = {'file': bpy.data.filepath, 'passed': all(checks.values()), 'parameters': VALUES,
             'age_color_srgb_hex': '#96988F', 'checks': checks}
    (OUT/'reopen_validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    assert audit['passed'], checks
    print('REFERENCE_COLOR_REOPEN ' + json.dumps(audit), flush=True)


if __name__ == '__main__':
    if '--verify' in sys.argv:
        verify()
    else:
        candidate()
