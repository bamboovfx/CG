"""只读重开主镜头，检查新五金链接/贴图并输出原机位样帧，不保存镜头设置。"""
import bpy
import json
from pathlib import Path

OUT=Path('D:/00_projects/10_CG/Shot_Test/06_review/window_hardware_pbr')
scene=bpy.context.scene
names=['ARC crescent cam.040','ARC curved latch handle.040','WIN pull grip.002']
assets={n:({'library':bpy.data.objects[n].library.filepath if bpy.data.objects[n].library else None,
            'materials':[m.name for m in bpy.data.objects[n].data.materials]}) if n in bpy.data.objects else None for n in names}
missing=[bpy.path.abspath(i.filepath,library=i.library) for i in bpy.data.images if i.source=='FILE' and not i.packed_file and i.filepath and not Path(bpy.path.abspath(i.filepath,library=i.library)).exists()]
report={'file':bpy.data.filepath,'frame':scene.frame_current,'fps':scene.render.fps,'range':[scene.frame_start,scene.frame_end],
        'actions':[a.name for a in bpy.data.actions],'assets':assets,'missing_textures':missing}
(OUT/'shot_link_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_percentage=50; scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/'shot_context.png')
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for dev in prefs.devices: dev.use=dev.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception: scene.cycles.device='CPU'
bpy.ops.render.render(write_still=True)
