"""重开候选后验证坐姿、资源和相机，输出 Workbench 低成本预览；不保存文件。"""
import bpy
import json
import sys
import hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/sh010_blocking_20260920'
REVIEW=ROOT/'06_review/sh010_blocking_20260920'
SOURCE=ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
report=json.loads((REVIEW/'build_report.json').read_text(encoding='utf-8'))
rest=json.loads((CACHE/'rest_pose.json').read_text(encoding='utf-8'))
scene=bpy.context.scene
errors=[]
missing=[]
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:
        path=Path(bpy.path.abspath(im.filepath,library=im.library))
        if not path.exists():
            missing.append(str(path))
libraries=[{'path':bpy.path.abspath(lib.filepath),'exists':Path(bpy.path.abspath(lib.filepath)).exists()} for lib in bpy.data.libraries]
samples=[]
for frame in [1001,1025,1071,1140]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    drift=max(abs(bpy.data.objects[n].matrix_world[r][c]-item['matrix_world'][r][c])
              for n,item in rest.items() for r in range(4) for c in range(4))
    errors.append(drift)
    values={}
    for lm in report['fit_landmarks']:
        p=world_to_camera_view(scene,scene.camera,Vector(lm['world_point']))
        values[lm['point']]=[p.x*1920,132+(1-p.y)*816]
    samples.append({'frame':frame,'root_geometry_matrix_drift':drift,'landmark_source_pixels':values})
source_ok=hashlib.sha256(SOURCE.read_bytes()).hexdigest()==report['source_hash']
assert source_ok and not missing and all(v['exists'] for v in libraries), {'source_ok':source_ok,'missing':missing,'libraries':libraries}
assert max(errors)<1e-5
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1001,1140,24)
validation={'reopened_candidate':bpy.data.filepath,'source_hash_unchanged':source_ok,
            'frames':[scene.frame_start,scene.frame_end],'frame_count':140,'fps':24,
            'duration_seconds':140/24,'missing_images':missing,'libraries':libraries,
            'character_instances':len(rest),'character_animation_actions':0,'sample_projections':samples,
            'max_rest_world_transform_error':max(errors),'video_complete':False,
            'visual_approval':'not approved; motion/shape discrepancies remain'}
(REVIEW/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')

# Workbench 仅用于核对构图/遮挡/时序，忽略最终透光和材质，不覆盖候选的渲染配置。
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO'
scene.display.shading.studiolight_rotate_z=.30
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.curvature_ridge_factor=1.35
scene.display.shading.curvature_valley_factor=1.05
scene.display.shading.background_type='WORLD'
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.render.use_compositing=False
scene.render.use_sequencer=False
scene.display.render_aa='8'
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'test'
if mode=='test':
    scene.render.resolution_x=640
    scene.render.resolution_y=270
    scene.frame_set(1071)
    scene.render.filepath=str(REVIEW/'probe_1071.png')
    bpy.ops.render.render(write_still=True)
else:
    scene.render.resolution_x=1280
    scene.render.resolution_y=540
    frames=REVIEW/'frames'
    frames.mkdir(exist_ok=True)
    scene.render.filepath=str(frames/'frame_')
    bpy.ops.render.render(animation=True)
print('REVEAL_PREVIEW_FINISHED',mode,flush=True)
