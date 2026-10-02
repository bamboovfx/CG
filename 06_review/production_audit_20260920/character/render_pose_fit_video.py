"""只渲染已完成的 pose_fit 候选全长灰模，编码并独立验证，不再修改姿态或保存场景。"""
import bpy
import json
import hashlib
import subprocess
from pathlib import Path

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/sh010_blocking_20260920'
CACHE=ROOT/'07_pipeline/cache/sh010_blocking_20260920'
CANDIDATE=CACHE/'pose_fit_candidate.blend'
SOURCE=ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
FRAMES=OUT/'pose_fit_frames'
VIDEO=OUT/'pose_fit_blocking.mp4'
FF=ROOT/'07_pipeline/cache/tools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
FRAMES.mkdir(exist_ok=True)
scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==CANDIDATE.resolve()
baseline=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
source_before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
candidate_before=hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
assert source_before==baseline['source_hash']
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1001,1140,24)
missing=[bpy.path.abspath(im.filepath,library=im.library) for im in bpy.data.images
         if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath,library=im.library)).exists()]
assert not missing,missing

# 与姿态返工三帧采用相同灰模设置，仅改变输出目录；不用此图判断最终光照材质。
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.render_aa='8'
scene.render.resolution_x=1280
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.use_compositing=False
scene.render.use_sequencer=False
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(FRAMES/'frame_')
bpy.ops.render.render(animation=True)
frames=sorted(FRAMES.glob('frame_*.png'))
assert [p.stem for p in frames]==[f'frame_{f}' for f in range(1001,1141)]
subprocess.run([str(FF),'-y','-hide_banner','-loglevel','error','-framerate','24','-start_number','1001',
                '-i',str(FRAMES/'frame_%04d.png'),'-frames:v','140','-c:v','libx264','-crf','18',
                '-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],check=True)
probe=subprocess.run([str(FF),'-hide_banner','-i',str(VIDEO),'-f','null','-'],capture_output=True,text=True)
assert probe.returncode==0 and 'frame=  140' in probe.stderr
(OUT/'pose_fit_video_decode_check.txt').write_text(probe.stderr,encoding='utf-8')
source_after=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
candidate_after=hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
assert source_before==source_after and candidate_before==candidate_after
validation={'candidate':str(CANDIDATE),'candidate_sha256':candidate_after,'candidate_file_unchanged':True,
            'canonical_source_sha256':source_after,'canonical_source_unchanged':True,
            'video':str(VIDEO),'video_sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
            'video_bytes':VIDEO.stat().st_size,'video_complete':True,'video_decode_success':True,
            'frame_range_inclusive':[1001,1140],'rendered_unique_png_count':140,
            'fps':24,'duration_seconds':140/24,'width':1280,'height':540,
            'missing_images':missing,'engine':'BLENDER_WORKBENCH','anti_alias_samples':8,
            'pose_changed_during_this_task':False,'new_character_action':False,
            'baseline_video_preserved':str(OUT/'blocking.mp4'),
            'beauty_stills_use':'baseline pose, not this revised pose',
            'limits':['Grey blocking preview only, not final lighting/materials.',
                      'Static revised seated pose; end-of-shot local acting still incomplete.']}
(OUT/'pose_fit_video_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print('POSE_FIT_FULL_VIDEO_COMPLETE',json.dumps(validation),flush=True)
