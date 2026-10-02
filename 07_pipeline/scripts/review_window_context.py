"""从用户当前镜头快照输出单帧上下文检查；不保存或修改正式镜头参数。"""
import bpy
from pathlib import Path

scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(Path('D:/00_projects/10_CG/Shot_Test/06_review/window_hardware_correction')/f'context_{scene.frame_current}.png')
# 后台评审使用可用OptiX设备，灯光、相机、帧数沿用用户快照。
try:
    pref=bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='OPTIX'; pref.get_devices()
    for device in pref.devices: device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception: scene.cycles.device='CPU'
bpy.ops.render.render(write_still=True)
