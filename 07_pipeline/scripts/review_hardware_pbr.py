"""在独立评审场景中检查五金的真实材质/UV；不保存临时灯光或改动用户姿态。"""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/window_hardware_pbr'


def render(label, mode='beauty', view='lock'):
    """输入输出标签、材质检查模式、锁/拉手视角；输出固定中性光PNG。"""
    OUT.mkdir(parents=True,exist_ok=True)
    objects=[o for o in bpy.data.collections['AST_window_wall_left'].all_objects]
    targets=[o for o in objects if o.type=='MESH' and o.get('window_hardware_20260927') and not o.name.startswith('CUT ')]
    if mode=='no_normal':
        for mat in {m for o in targets for m in o.data.materials if m}:
            if not mat.use_nodes: continue
            for node in mat.node_tree.nodes:
                if node.type=='BSDF_PRINCIPLED':
                    for link in list(node.inputs['Normal'].links): mat.node_tree.links.remove(link)
    if mode=='checker':
        mat=bpy.data.materials.new('UV inspection'); mat.use_nodes=True
        ns=mat.node_tree.nodes; ls=mat.node_tree.links; bs=ns.get('Principled BSDF')
        uv=ns.new('ShaderNodeUVMap'); uv.uv_map=targets[0].data.uv_layers.active.name
        checker=ns.new('ShaderNodeTexChecker'); checker.inputs['Scale'].default_value=64
        checker.inputs['Color1'].default_value=(.035,.09,.2,1); checker.inputs['Color2'].default_value=(.65,.8,.95,1)
        ls.new(uv.outputs['UV'],checker.inputs['Vector']); ls.new(checker.outputs['Color'],bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value=.8
        for o in targets:
            o.data=o.data.copy(); o.data.materials.clear(); o.data.materials.append(mat)
    scene=bpy.data.scenes.new('Hardware PBR review')
    for o in objects: scene.collection.objects.link(o)
    world=bpy.data.worlds.new('Neutral studio'); world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.38,.38,.38,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4; scene.world=world
    target=Vector((-3.974,-3.44,1.609)) if view=='lock' else Vector((-3.95,-3.4575,1.48))
    cd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',cd); scene.collection.objects.link(cam)
    offset=Vector((.036,.23,.028)) if view=='lock' else Vector((.23,.1,.026))
    cam.location=target+offset; cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cd.type='ORTHO'; cd.ortho_scale=.108 if view=='lock' else .178; cd.clip_start=.001; scene.camera=cam
    for offset,power,size in [((.12,.18,.2),3,.2),((-.1,.15,.03),1,.14)]:
        ld=bpy.data.lights.new('Area','AREA'); ld.energy=power; ld.shape='RECTANGLE'; ld.size=size; ld.size_y=size*.65
        ob=bpy.data.objects.new('Area',ld); scene.collection.objects.link(ob); ob.location=target+Vector(offset)
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='OPTIX'; pref.get_devices()
        for dev in pref.devices: dev.use=dev.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception: scene.cycles.device='CPU'
    scene.render.resolution_x=1000; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/(label+'.png'))
    bpy.ops.render.render(write_still=True,scene=scene.name)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    render(*args)
