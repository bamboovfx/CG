"""输出一轮姿态修正三方对照：原片、视频所用 baseline、静态 pose fit。"""
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/sh010_blocking_20260920'
REF=ROOT/'06_review/production_audit_20260920/hero_motion_frames'
sheet=Image.new('RGB',(1920,900),'#171b1d')
draw=ImageDraw.Draw(sheet)
for row,(source,frame) in enumerate([(3823,1001),(3893,1071),(3962,1140)]):
    reference=Image.open(REF/f'source_{source:06d}.png').convert('RGB').crop((0,132,1920,948))
    baseline=Image.open(OUT/'frames'/f'frame_{frame}.png').convert('RGB')
    fitted=Image.open(OUT/f'pose_fit_{frame}.png').convert('RGB')
    for col,(im,label) in enumerate([(reference,'REFERENCE'),(baseline,'BASELINE video'),(fitted,'POSE FIT revised video')]):
        sheet.paste(im.resize((640,270),Image.Resampling.LANCZOS),(col*640,row*300))
        draw.text((col*640+10,row*300+276),f'{label} / frame {frame}',fill='white')
sheet.save(OUT/'comparison_pose_fit.jpg',quality=95)
print('POSE_COMPARISON_READY')
