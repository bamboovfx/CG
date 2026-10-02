"""Measure image-space displacement with small normalized-correlation patches; this is not a camera solve."""
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw
out=Path(r'D:/00_projects/10_CG/Shot_Test/06_review/production_audit_20260920');folder=out/'hero_motion_frames'


def track(template_image,target_image,point,dx_range,half=17):
    """Input grayscale arrays, seed pixel and dx search range; return best integer-pixel NCC point/score."""
    x,y=point;t=template_image[y-half:y+half+1,x-half:x+half+1].astype(float);t-=t.mean();tn=np.sqrt((t*t).sum());best=(-2,None)
    for dy in range(-7,8):
        for dx in range(*dx_range):
            p=target_image[y+dy-half:y+dy+half+1,x+dx-half:x+dx+half+1].astype(float);p-=p.mean();pn=np.sqrt((p*p).sum());score=float((p*t).sum()/(tn*pn+1e-8))
            if score>best[0]:best=(score,[x+dx,y+dy])
    return {'xy':best[1],'ncc':round(best[0],5)}


frames=[3823,3893,3962];images={f:np.asarray(Image.open(folder/f'source_{f:06d}.png').convert('L')) for f in frames}
points={'clock_center':(652,282),'blackboard_top_right':(1098,318),'tv_lower_left':(408,428),'small_sign_above_board':(1063,298)}
result={}
for name,point in points.items():
    result[name]={'3823':{'xy':list(point),'ncc':1.0}}
    result[name]['3893']=track(images[3823],images[3893],point,(60,115))
    result[name]['3962']=track(images[3823],images[3962],point,(135,200))
# Draw review markers on an audit copy, making mistaken feature matches visible.
for f in frames:
    im=Image.open(folder/f'source_{f:06d}.png').convert('RGB');d=ImageDraw.Draw(im)
    for i,(name,rs) in enumerate(result.items(),1):
        x,y=rs[str(f)]['xy'];d.ellipse((x-6,y-6,x+6,y+6),outline='#ff40ff',width=2);d.text((x+9,y+6),f'{i}: {x},{y}',fill='#ff40ff')
    im.save(out/f'hero_tracked_{f}.jpg',quality=95)
(out/'hero_tracks_raw.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
