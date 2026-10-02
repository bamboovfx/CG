"""真实渲染共享集合实例的木纹／磨损变化，并用同机位发光诊断验证种子确实改变内容。"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_scene_chairs import OUT, MASTER, dump
from replace_scene_chairs import layer_kind
from wood_layers_blender import aim


def setup():
    """输入共享母资产，输出只供本进程渲染的三实例工作室与相机；不保存临时场景。"""
    original = bpy.context.scene
    sc = bpy.data.scenes.new('REVIEW / instances'); bpy.context.window.scene = sc
    sc.render.engine = 'CYCLES'; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = original.view_settings.view_transform
    sc.view_settings.look = original.view_settings.look; sc.view_settings.exposure = -.25
    world = bpy.data.worlds.new('REVIEW / neutral'); world.use_nodes = True; sc.world = world
    world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.1,.1,.1,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .3
    roots = []
    for index, name in enumerate(['asset_desk_set_01_chair','asset_desk_set_02_chair','asset_desk_set_03_chair']):
        source = bpy.data.objects[name]; ob = source.copy(); sc.collection.objects.link(ob)
        ob.name = 'REVIEW / chair ' + str(index+1)
        ob.matrix_world = Matrix.Translation(((index-1)*.62,0,.0205)) @ Matrix.Diagonal((1.1231344,)*3+(1,))
        roots.append(ob)
    for pos, power, size in [((1.7,2.3,3),600,2.5),((-2,1.3,2),260,3),((0,-2,2.5),450,2)]:
        data = bpy.data.lights.new('Area', 'AREA'); data.energy = power; data.shape = 'DISK'; data.size = size
        ob = bpy.data.objects.new('Area',data); sc.collection.objects.link(ob); ob.location = pos; aim(ob,(0,0,.45))
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,.0205)); plane = bpy.context.object
    mat = bpy.data.materials.new('REVIEW / floor'); mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value = (.17,.17,.17,1)
    p.inputs['Roughness'].default_value = .85; plane.data.materials.append(mat)
    camera = bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); sc.collection.objects.link(camera); sc.camera = camera
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'CUDA'; prefs.get_devices()
    for device in prefs.devices: device.use = device.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.seed = 177; sc.render.image_settings.color_depth = '8'
    return sc, roots, camera, plane


def render(sc, camera, name, pos, target, width, height, lens, samples=32):
    """输入透视机位、尺寸和采样，输出实际PNG并保留每帧用时／内存的渲染日志。"""
    camera.location = pos; aim(camera, target); camera.data.lens = lens
    sc.render.resolution_x = width; sc.render.resolution_y = height; sc.render.resolution_percentage = 100
    sc.cycles.samples = samples; sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = str(OUT / (name+'.png')); bpy.ops.render.render(write_still=True)
    print('INSTANCES_RENDERED', name, flush=True)


def diagnostics(sc, roots, camera, plane):
    """输入同一实例和共享材质，分别改变Wear／Grain种子，比较真实着色像素且检查另外种子不变。"""
    roots[0].hide_render = True; roots[2].hide_render = True; plane.hide_render = True
    target = roots[1]
    mats = {m for o in bpy.data.collections[MASTER].objects for m in o.data.materials if m}
    saved = {}; diagnostic = {}
    for mat in mats:
        t = mat.node_tree; out = next(n for n in t.nodes if n.type == 'OUTPUT_MATERIAL')
        saved[mat] = out.inputs['Surface'].links[0].from_socket
        e = t.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0,0,0,1)
        t.links.new(e.outputs[0], out.inputs['Surface']); diagnostic[mat] = e
    sc.cycles.use_denoising = False; sc.render.film_transparent = True
    sc.render.resolution_x = 620; sc.render.resolution_y = 620
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.cycles.samples = 4
    sc.view_settings.exposure = 0
    camera.location = (.5,1.5,1.12); aim(camera,(0,0,.51)); camera.data.lens = 55
    for mode, prop in [('wear','Seed Wear'), ('grain','Seed Grain')]:
        for mat, e in diagnostic.items():
            for l in list(e.inputs['Color'].links): mat.node_tree.links.remove(l)
            e.inputs['Color'].default_value = (0,0,0,1)
            for n in mat.node_tree.nodes:
                if n.type != 'GROUP': continue
                kind, _ = layer_kind(n)
                if mode == 'wear' and kind == 'metal':
                    mat.node_tree.links.new(n.outputs['Chip Mask'], e.inputs['Color'])
                if mode == 'grain' and n.get('wood_layers_role') == 'process':
                    mat.node_tree.links.new(n.outputs['Color'], e.inputs['Color'])
        original = target[prop]; arrays = []
        for label, seed in [('a',original), ('b',original+179)]:
            target[prop] = seed; target.update_tag(); bpy.context.view_layer.update()
            path = OUT / (mode+'_seed_'+label+'.exr'); sc.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(str(path)); arrays.append(np.array(im.pixels[:],dtype=np.float32).reshape(620,620,4))
        target[prop] = original
        a, b = arrays; active = np.maximum(a[:,:,:3],b[:,:,:3]).max(axis=2) > .02
        delta = np.abs(a[:,:,:3]-b[:,:,:3]).mean(axis=2)
        changed = int(((delta>.025)&active).sum()); count = int(active.sum())
        audit = {'property': prop, 'seed_a': original, 'seed_b': original+179,
            'active_pixels': count, 'changed_pixels': changed, 'changed_fraction': changed/max(count,1),
            'mean_absolute_change': float(delta[active].mean()) if count else 0,
            'passed': count>100 and changed/max(count,1)>.10}
        dump(OUT / (mode+'_seed_probe.json'), audit)
        assert audit['passed'], audit
        print('ACTUAL_SEED_DIAGNOSTIC', audit, flush=True)
    for mat, original in saved.items():
        mat.node_tree.links.new(original, next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
        mat.node_tree.nodes.remove(diagnostic[mat])


def main():
    """输入独立重开的共享实例候选，输出整体／金属／木纹同光图和Seed像素证据；不保存评审变化。"""
    sc, roots, camera, plane = setup()
    render(sc,camera,'variants',(1.35,2.85,1.55),(0,0,.45),1600,1000,53)
    render(sc,camera,'metal_wear',(0,2.55,1.12),(0,-.205,.86),1700,560,52)
    render(sc,camera,'wood_grain',(.55,2.45,2.55),(0,0,.44),1700,760,52)
    diagnostics(sc,roots,camera,plane)


def classroom():
    """输入正式教室候选，沿用原灯光与帧并暂用已有室内相机；输出实例整合图，退出不保存。"""
    sc = bpy.context.scene; sc.camera = bpy.data.objects['cam_sh010_main']
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'CUDA'; prefs.get_devices()
    for device in prefs.devices: device.use = device.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.samples = 8; sc.cycles.seed = 177
    sc.render.resolution_x = 960; sc.render.resolution_y = 406; sc.render.resolution_percentage = 100
    sc.render.image_settings.color_depth = '8'; sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = str(OUT / 'classroom.png'); bpy.ops.render.render(write_still=True)
    print('CLASSROOM_INSTANCES_RENDERED', flush=True)


if __name__ == '__main__':
    if '--classroom' in sys.argv: classroom()
    else: main()
