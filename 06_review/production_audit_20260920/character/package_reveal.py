"""编码140帧预览、复制检查帧并制作原片/候选对照；不更改任何 Blender 数据。"""
import json
import hashlib
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/sh010_blocking_20260920'
AUDIT=ROOT/'06_review/production_audit_20260920'
FF=ROOT/'07_pipeline/cache/tools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
frames=OUT/'frames'
existing=sorted(frames.glob('frame_*.png'))
assert [p.stem for p in existing]==[f'frame_{f}' for f in range(1001,1141)]
video=OUT/'blocking.mp4'
subprocess.run([str(FF),'-y','-hide_banner','-loglevel','error','-framerate','24','-start_number','1001',
                '-i',str(frames/'frame_%04d.png'),'-frames:v','140','-c:v','libx264','-crf','18',
                '-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
probe=subprocess.run([str(FF),'-hide_banner','-i',str(video),'-f','null','-'],capture_output=True,text=True)
assert probe.returncode==0
(OUT/'video_decode_check.txt').write_text(probe.stderr,encoding='utf-8')
for f,label in [(1001,'start'),(1071,'middle'),(1140,'end')]:
    shutil.copy2(frames/f'frame_{f}.png',OUT/f'blocking_{label}_{f}.png')
for mode in ['blocking','beauty']:
    # 对照板按原片有效画面裁切，不将播放器黑边烘焙到候选视频。
    sheet=Image.new('RGB',(1280,3*300),'#171b1d')
    draw=ImageDraw.Draw(sheet)
    for row,(source,production) in enumerate([(3823,1001),(3893,1071),(3962,1140)]):
        ref=Image.open(AUDIT/'hero_motion_frames'/f'source_{source:06d}.png').convert('RGB')
        ref=ref.crop((0,132,1920,948)).resize((640,270),Image.Resampling.LANCZOS)
        candidate_path=OUT/f'beauty_{production}.png' if mode=='beauty' else frames/f'frame_{production}.png'
        if not candidate_path.exists():
            break
        candidate=Image.open(candidate_path).convert('RGB').resize((640,270),Image.Resampling.LANCZOS)
        y=row*300
        sheet.paste(ref,(0,y));sheet.paste(candidate,(640,y))
        draw.text((10,y+274),f'REFERENCE source {source} / production {production}',fill='white')
        draw.text((650,y+274),f'CANDIDATE {mode.upper()} / production {production}',fill='white')
    else:
        sheet.save(OUT/f'comparison_{mode}.jpg',quality=94)
validation=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
validation.update({'video_complete':True,'video':str(video),'video_bytes':video.stat().st_size,
                   'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
                   'rendered_png_count':len(existing),'video_decode_success':True,
                   'video_width':1280,'video_height':540,
                   'beauty_frames_complete':all((OUT/f'beauty_{f}.png').exists() for f in [1001,1071,1140]),
                   'video_look':'Workbench grey preview; separate Cycles stills assess lighting and materials'})
(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print('BLOCKING_VIDEO_PACKAGED',video,flush=True)
