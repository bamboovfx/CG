"""拼合同机位材质前后，不编辑原贴图；读回关闭印记的隔离渲染以记录差异。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'06_review/tripo_wood_side_back_20260930'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
pairs=[('side_comparison.jpg','侧立面／原有等宽条带','00_side_before.png','侧立面／独立侧壁UV','05_side_after.png'),
    ('back_comparison.jpg','背面／遗留程序矩形','01_back_before.png','背面／关闭印记分支','06_back_after.png'),
    ('corner_comparison.jpg','转角／修复前','02_corner_before.png','转角／侧壁连续细纹','07_corner_after.png')]
for filename,left,a,right,b in pairs:
    canvas=Image.new('RGB',(1600,558),(25,25,25)); draw=ImageDraw.Draw(canvas)
    for index,(label,file) in enumerate([(left,a),(right,b)]):
        canvas.paste(Image.open(OUT/file).convert('RGB').resize((800,500),Image.Resampling.LANCZOS),(index*800,58))
        draw.text((index*800+16,13),label,font=font,fill='white')
    canvas.save(OUT/filename,quality=97)
# 只关闭stamp的背面图与最终背面图几乎一致，证明矩形消失来自颜色分支。
stamp=np.asarray(Image.open(OUT/'04_back_stamp_off.png'),dtype=np.int16)
final=np.asarray(Image.open(OUT/'06_back_after.png'),dtype=np.int16)
before=np.asarray(Image.open(OUT/'01_back_before.png'),dtype=np.int16)
delta=np.abs(before-stamp); delta_final=np.abs(final-stamp)
audit={'stamp_off_vs_before':{'max':int(delta.max()),'fraction_gt_5':float((delta>5).mean())},
    'stamp_off_vs_final':{'max':int(delta_final.max()),'mean':float(delta_final.mean()),'fraction_gt_5':float((delta_final>5).mean())}}
(OUT/'isolation_comparison.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('SIDE_BACK_REVIEW '+json.dumps(audit),flush=True)
