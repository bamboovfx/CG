"""顺序渲染候选首中末三张 Cycles 彩色评审；保留当前源 World/材质，不保存场景。"""
import bpy
from pathlib import Path

OUT=Path('D:/00_projects/10_CG/Shot_Test/06_review/sh010_blocking_20260920')
scene=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use=device.type!='CPU'
scene.render.engine='CYCLES'
scene.cycles.device='GPU'
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.use_persistent_data=True
scene.render.resolution_x=1280
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.use_border=False
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
for frame in [1001,1071,1140]:
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'beauty_{frame}.png')
    bpy.ops.render.render(write_still=True)
    print('BEAUTY_FRAME_COMPLETE',frame,flush=True)
print('REVEAL_BEAUTY_FINISHED',flush=True)
