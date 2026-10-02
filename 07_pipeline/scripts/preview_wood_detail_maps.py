"""组合原始资产和SD输出的评审缩略图／1:1裁片，不修改任何材质图。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_detail_20260930'; OUT.mkdir(parents=True,exist_ok=True)
TEX=ROOT/'02_assets/textures/generated/tripo_wood_detail/seat'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)

def preview(path):
    """输入PNG/JPG，按真实16位灰度范围显示评审图，避免直接转RGB被钳成白色。"""
    im=Image.open(path)
    if im.mode in ('I','I;16','I;16B'):
        im=Image.fromarray((np.asarray(im,dtype=np.uint16)//257).astype(np.uint8),'L')
    return im.convert('RGB')
items=[('旧漆木桌／色差和磨痕','wood_table_worn'),('拼板旧木／小磕碰和嵌色','wood_table_large'),('完整涂层／细纤维与反射','wood_table_001')]
canvas=Image.new('RGB',(1536,570),(25,25,25)); draw=ImageDraw.Draw(canvas)
for index,(label,asset) in enumerate(items):
    path=ROOT/'02_assets/textures/external/polyhaven_wood_detail'/asset/(asset+'_diff_1k.jpg')
    im=Image.open(path).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    canvas.paste(im,(index*512,58)); draw.text((index*512+10,12),label,font=font,fill='white')
canvas.save(OUT/'reference_study.jpg',quality=94)
channels=['Raw_AgeColor','Raw_WearColor','Raw_DirtColor','Raw_AgeMask','Raw_WearMask','Raw_AgeHeight']
canvas=Image.new('RGB',(1536,1140),(25,25,25)); draw=ImageDraw.Draw(canvas)
for index,name in enumerate(channels):
    im=preview(TEX/(name+'.png')).resize((512,512),Image.Resampling.LANCZOS)
    x=index%3*512; y=index//3*570
    canvas.paste(im,(x,y+58)); draw.text((x+10,y+12),name,font=font,fill='white')
canvas.save(OUT/'raw_map_study.jpg',quality=94)
# 1:1裁片明确对应约46mm木板区域，不以缩略图代替细节验收。
channels=['BaseColor','Roughness','Raw_AgeHeight']
canvas=Image.new('RGB',(1536,570),(25,25,25)); draw=ImageDraw.Draw(canvas)
for index,name in enumerate(channels):
    im=preview(TEX/(name+'.png')).crop((1100,800,1612,1312))
    canvas.paste(im,(index*512,58)); draw.text((index*512+10,12),name+' / 1:1',font=font,fill='white')
canvas.save(OUT/'map_100_percent.jpg',quality=97)
