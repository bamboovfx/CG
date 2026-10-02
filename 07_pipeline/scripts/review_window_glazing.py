"""从当前镜头恢复副本渲染相同斜视机位，比较胶条修正；不保存相机或灯光。"""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
mode=sys.argv[sys.argv.index('--')+1]
lib=next(l for l in bpy.data.libraries if 'classroom_environment.blend' in l.filepath)
lib.filepath=str(ROOT/'07_pipeline/cache/window_glazing'/('source_before.blend' if mode=='before' else 'candidate.blend'));lib.reload()
s=bpy.context.scene
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);s.collection.objects.link(cam)
cam.location=(1.9,-1.3,1.95);target=Vector((4,1.65,2.02))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=48;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.resolution_x=1280;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'06_review/window_glazing'/(mode+'.png'))
bpy.ops.render.render(write_still=True)
