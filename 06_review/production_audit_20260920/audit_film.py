"""Audit only: decode low-resolution reference evidence; never modify source media or DCC scenes."""
from pathlib import Path
import json, re, subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw

ROOT = Path(r'D:/00_projects/10_CG/Shot_Test')
OUT = ROOT/'06_review/production_audit_20260920'
VIDEO = ROOT/'01_preproduction/references/video/drop_official_1080p.mp4'
FF = imageio_ffmpeg.get_ffmpeg_exe()


def tc(frame):
    """Convert a zero-based source frame number into 24 fps HH:MM:SS:FF."""
    return f'{frame//86400:02d}:{frame//1440%60:02d}:{frame//24%60:02d}:{frame%24:02d}'


def sheet(items, name, columns=3):
    """Combine (frame number, label) evidence into a labelled JPEG without changing original video."""
    canvas = Image.new('RGB', (480*columns, 300*((len(items)+columns-1)//columns)), '#151515')
    draw = ImageDraw.Draw(canvas)
    for i,(frame,label) in enumerate(items):
        x,y = (i%columns)*480,(i//columns)*300
        im = Image.open(OUT/'frames'/f'f{frame:06d}.jpg')
        canvas.paste(im,(x,y))
        draw.text((x+8,y+272),f'{label} | {tc(frame)} | {frame/24:.6f}s',fill='white')
    canvas.save(OUT/name,quality=92)


text = (OUT/'scene_detection_018.txt').read_text(encoding='utf-8')
cut_frames = [round(float(v)*24) for v in re.findall(r'pts_time:([0-9.]+)',text)]
# Dense half-second samples test the classroom action; sparse samples locate the entire film.
class_frames = list(range(140*24,176*24,12))
wide_frames = list(range(0,251*24,5*24))
pairs = sorted({n for f in cut_frames for n in (f-1,f)})
wanted = set(class_frames+wide_frames+pairs)
(OUT/'frames').mkdir(exist_ok=True)
reader = imageio_ffmpeg.read_frames(str(VIDEO),pix_fmt='rgb24',output_params=['-vf','scale=480:270'])
meta = next(reader)
count = 0
for count,data in enumerate(reader,1):
    frame = count-1
    if frame in wanted:
        Image.frombytes('RGB',(480,270),data).save(OUT/'frames'/f'f{frame:06d}.jpg',quality=90)
meta['decoded_frames'] = count
meta['duration_from_frames'] = count/24
meta['audio_streams'] = 0
meta['timecode_basis'] = 'zero-based source frame at constant 24 fps; ends are exclusive'
(OUT/'verified_media.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
(OUT/'detected_boundaries.json').write_text(json.dumps([{'frame':f,'seconds':f/24,'timecode':tc(f),'status':'candidate_pending_visual_review'} for f in cut_frames],indent=2),encoding='utf-8')
for i in range(0,len(cut_frames),9):
    sheet([(n,label) for j,f in enumerate(cut_frames[i:i+9],i+1) for n,label in [(f-1,f'C{j:02d} PRE'),(f,f'C{j:02d} POST')]],f'cut_pairs_{i//9+1:02d}.jpg',2)
for i in range(0,len(wide_frames),18):
    sheet([(f,'OVERVIEW') for f in wide_frames[i:i+18]],f'overview_{i//18+1:02d}.jpg')
for i in range(0,len(class_frames),18):
    sheet([(f,'CLASSROOM') for f in class_frames[i:i+18]],f'classroom_motion_{i//18+1:02d}.jpg')
print(json.dumps(meta,indent=2))
