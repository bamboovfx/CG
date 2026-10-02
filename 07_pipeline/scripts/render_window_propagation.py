"""独立评审灯光下检查镜像五金、整个窗组与删除占位块后的边框；不保存评审状态。"""
import bpy,sys
from pathlib import Path
from mathutils import Vector
OUT=Path('D:/00_projects/10_CG/Shot_Test/06_review/window_propagation')


def render(view):
    """输入lock/window视角，输出同一候选的近景或完整窗组评审图。"""
    scene=bpy.data.scenes.new('Window propagation review')
    for o in bpy.data.collections['AST_window_wall_corridor'].objects:scene.collection.objects.link(o)
    world=bpy.data.worlds.new('Review World');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.4,.4,.4,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35;scene.world=world
    target=Vector((3.985,-4.94,1.55)) if view=='lock' else Vector((4,-4.2,2.17))
    offset=Vector((-.045,.24,.035)) if view=='lock' else Vector((-5,.5,.3))
    cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);scene.collection.objects.link(cam)
    cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    cd.type='ORTHO';cd.ortho_scale=.13 if view=='lock' else 3.55;cd.clip_start=.001
    for off,power,size in [((-.3,.35,.4),3,.25),((-.25,-.25,.15),1,.18)]:
        if view!='lock':off=tuple(v*8 for v in off);power*=150;size*=8
        ld=bpy.data.lights.new('Area','AREA');ld.energy=power;ld.size=size
        ob=bpy.data.objects.new('Area',ld);scene.collection.objects.link(ob);ob.location=target+Vector(off);ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for dev in prefs.devices:dev.use=dev.type=='OPTIX'
    scene.cycles.device='GPU';scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/(view+'.png'))
    bpy.ops.render.render(write_still=True,scene=scene.name)


if __name__=='__main__':render(sys.argv[sys.argv.index('--')+1])
