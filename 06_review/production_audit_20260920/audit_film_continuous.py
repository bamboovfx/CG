"""Decode focused audit samples only; preserve the copyrighted source and all DCC files."""
from pathlib import Path
from PIL import Image, ImageDraw
import imageio_ffmpeg
ROOT=Path(r'D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/production_audit_20260920'


def sheet(frames,name,columns=3):
    """Build a labelled review sheet from source-frame numbers; output is audit evidence only."""
    im=Image.new('RGB',(480*columns,300*((len(frames)+columns-1)//columns)),'#151515');d=ImageDraw.Draw(im)
    for i,f in enumerate(frames):
        x,y=(i%columns)*480,(i//columns)*300
        im.paste(Image.open(OUT/'frames'/f'f{f:06d}.jpg'),(x,y))
        d.text((x+8,y+272),f'Frame {f} | {f//1440:02d}:{f//24%60:02d}:{f%24:02d} | {f/24:.6f}s',fill='white')
    im.save(OUT/name,quality=92)


# Dense review covers long apparent takes and the previously unverified dark scenes.
ranges={'shop':list(range(51*24,89*24,24)), 'dark':list(range(177*24,215*24,12)), 'ending':list(range(214*24,251*24,12))}
want={f for values in ranges.values() for f in values}
reader=imageio_ffmpeg.read_frames(str(ROOT/'01_preproduction/references/video/drop_official_1080p.mp4'),pix_fmt='rgb24',output_params=['-vf','scale=480:270'])
next(reader)
for f,data in enumerate(reader):
    if f in want:
        p=OUT/'frames'/f'f{f:06d}.jpg'
        if not p.exists():Image.frombytes('RGB',(480,270),data).save(p,quality=90)
for label,frames in ranges.items():
    for i in range(0,len(frames),18):sheet(frames[i:i+18],f'{label}_continuity_{i//18+1:02d}.jpg')
print('continuity sheets ready')
