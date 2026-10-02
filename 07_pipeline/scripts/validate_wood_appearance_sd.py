"""验证SD表现层归零、工艺图哈希和同光渲染基线；不修改任何源图。"""
from pathlib import Path
import subprocess
import hashlib
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_appearance_20260930'
WORK=ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930'
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
manifest=json.loads((ROOT/'02_assets/textures/generated/tripo_wood_appearance/manifest.json').read_text(encoding='utf-8'))
results=[]
for board in manifest['boards']:
    dest=WORK/('zero_'+board['board']); dest.mkdir(exist_ok=True)
    command=[str(SD/'sbsrender.exe'),'render','--inputs',str(ROOT/board['source']).replace('.sbs','.sbsar'),
        '--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@10,10',
        '--set-value','Scratches@0','--set-value','Age@0','--set-value','Wear@0','--engine','d3d11','--output-bit-depth','16','--no-report']
    done=subprocess.run(command,capture_output=True,text=True)
    (WORK/(board['board']+'_zero.log')).write_text(done.stdout+done.stderr,encoding='utf-8')
    assert done.returncode==0,(done.stdout+done.stderr)[-2000:]
    maxima={name:int(np.asarray(Image.open(dest/(name+'.png'))).max()) for name in board['outputs'] if not name.startswith('Raw_')}
    assert all(value==0 for value in maxima.values()),maxima
    results.append({'board':board['board'],'zero_output_maxima':maxima})
protected={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['protected_process_files'].items()}
assert all(protected.values())
# 同样本种子、同机位比较工艺层，记录微小浮点法线归一化带来的像素差。
a=np.asarray(Image.open(OUT/'01_process_before.png'),dtype=np.int16)
b=np.asarray(Image.open(OUT/'02_process_after.png'),dtype=np.int16)
delta=np.abs(a-b)
audit={'zero_controls':results,'process_files_unchanged':protected,
       'process_render_8bit_difference':{'max':int(delta.max()),'mean':float(delta.mean()),'fraction_over_2':float((delta>2).mean())}}
(OUT/'sd_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26)
# 仅组合已渲染评审图，不修改参考照片或材质贴图。
for filename,items in [('appearance_comparison.jpg',[('上一版','00_before_seat.png'),('表现层加强','03_after_seat.png')]),
                       ('highlight_comparison.jpg',[('上一版高光','00_before_highlight.png'),('新版高光','06_after_highlight.png')]),
                       ('appearance_isolation.jpg',[('工艺层','02_process_after.png'),('只开老化','07_age_only.png'),('只开磨损','08_wear_only.png')])]:
    width=700 if len(items)==2 else 560
    canvas=Image.new('RGB',(width*len(items),width+60),(28,28,28)); draw=ImageDraw.Draw(canvas)
    for index,(label,name) in enumerate(items):
        im=Image.open(OUT/name).convert('RGB').resize((width,width),Image.Resampling.LANCZOS)
        canvas.paste(im,(index*width,60)); draw.text((index*width+20,14),label,font=font,fill=(238,238,238))
    canvas.save(OUT/filename,quality=94)
print(json.dumps(audit,ensure_ascii=False),flush=True)
