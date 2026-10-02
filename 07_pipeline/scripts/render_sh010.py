"""在 CLI 中渲染当前镜头；参数为 preview/beauty，不改写工作工程。"""
import bpy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
scene=bpy.context.scene
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'preview'
version=scene.get('production_version','v001')
# 显式启用本机 GPU，避免后台进程继承错误的设备偏好。
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type!='CPU'
scene.cycles.device='GPU'
scene.render.resolution_percentage=75 if mode=='preview' else 100
scene.cycles.samples=48 if mode=='preview' else 384
path=ROOT/f'04_renders/sq010/sh010/{mode}/{version}/drop_sq010_sh010_{mode}_{version}.png'
path.parent.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(path)
bpy.ops.render.render(write_still=True)
print('RENDER_WRITTEN',path,flush=True)
if mode=='beauty':
    # 同一 Render Result 另存线性 half-float EXR，后续调色无需重渲染。
    scene.render.image_settings.file_format='OPEN_EXR'
    scene.render.image_settings.color_depth='16'
    scene.render.image_settings.exr_codec='ZIP'
    bpy.data.images['Render Result'].save_render(str(path.with_suffix('.exr')),scene=scene)
    print('LINEAR_EXR_WRITTEN',path.with_suffix('.exr'),flush=True)
