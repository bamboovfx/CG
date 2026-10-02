"""临时评审场景渲染：复用真实资产/材质，不将评审灯光写回建筑源。"""
import bpy
import sys
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/window_hardware_correction'


def render_review(label, opened=False, overview=False):
    """输入输出标签和开闭状态，渲染真实模型近景；仅后台内存中调整评审状态。"""
    source=bpy.context.scene
    ctrl=bpy.data.objects['ctrl_window_left_04']
    ctrl.location.y=-.21707811951637268 if opened else 0
    rig=bpy.data.objects.get('ctrl_window_lock_02')
    if rig: rig.rotation_euler.y=math.pi if opened else 0
    bpy.context.view_layer.update()
    scene=bpy.data.scenes.new('Hardware review')
    # 仅在临时场景布光，保留正式材质的纹理与节点。
    for ob in bpy.data.collections['AST_window_wall_left'].all_objects:
        scene.collection.objects.link(ob)
    world=bpy.data.worlds.new('Review neutral'); world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.55,.6,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
    scene.world=world
    target=Vector((-3.98,-3.46,1.55))
    cd=bpy.data.cameras.new('Review Camera'); cam=bpy.data.objects.new('Review Camera',cd)
    scene.collection.objects.link(cam)
    cam.location=target+Vector((.42,.32,.13)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cd.type='ORTHO'; cd.ortho_scale=.32 if not opened else .52; cd.clip_start=.001; cd.clip_end=100
    if overview:
        target=Vector((-4,-3.95,1.95)); cam.location=target+Vector((4.5,1.4,.7))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cd.ortho_scale=3.6
    scene.camera=cam
    for i,(offset,power,size) in enumerate([((.3,.4,.4),12,.5),((.25,-.4,.1),8,.45)]):
        ld=bpy.data.lights.new('Review Area','AREA'); ld.energy=power; ld.shape='DISK'; ld.size=size
        lo=bpy.data.objects.new('Review Area',ld); scene.collection.objects.link(lo)
        lo.location=target+Vector(offset); lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES'; scene.cycles.samples=40; scene.cycles.use_denoising=True
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='OPTIX'; pref.get_devices()
        for dev in pref.devices: dev.use=dev.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception: scene.cycles.device='CPU'
    scene.render.resolution_x=1200; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'
    scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/(label+'.png'))
    scene.render.film_transparent=False
    bpy.ops.render.render(write_still=True,scene=scene.name)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    render_review(args[0],opened='open' in args,overview='overview' in args)
