"""检查SD全图金属度与表现层归零；生成参考／渲染评审版式，不编辑材质图。"""
from pathlib import Path
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
TEX=ROOT/'02_assets/textures/generated/tripo_wood_reference'
WORK=ROOT/'07_pipeline/cache/tripo_wood_reference_20260930'
OUT=ROOT/'06_review/tripo_wood_reference_20260930'


def check():
    """读SD清单，以1K验证参数归零，并检查实际4K木材金属度全图为0。"""
    manifest=json.loads((TEX/'manifest.json').read_text(encoding='utf-8')); boards=[]
    for item in manifest['boards']:
        board=item['board']; folder=WORK/'zero_controls'/board; folder.mkdir(parents=True,exist_ok=True)
        command=item['commands'][1].copy(); command[command.index('--output-path')+1]=str(folder)
        command[command.index('$outputsize@12,12')]='$outputsize@10,10'
        for name in ('Scratches','Age','Wear'): command.extend(['--set-value',name+'@0'])
        done=subprocess.run(command,capture_output=True,text=True)
        (folder/'render_result.txt').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-2500:])
        differences={name:int(np.abs(np.asarray(Image.open(folder/(name+'.png')),dtype=np.int32)-np.asarray(Image.open(folder/('Process_'+name+'.png')),dtype=np.int32)).max()) for name in ('BaseColor','Roughness','Metallic','Normal','AO')}
        metallic=np.asarray(Image.open(TEX/board/'Metallic.png')); ao=np.asarray(Image.open(TEX/board/'AO.png'))
        boards.append({'board':board,'zero_max_pixel_difference':differences,'metallic_extrema':[int(metallic.min()),int(metallic.max())],'ao_extrema':[int(ao.min()),int(ao.max())],'passed':bool(max(differences.values())==0 and metallic.max()==0)})
        for channel in ('Process_Roughness','Process_Normal','Process_Height'):
            data=np.asarray(Image.open(TEX/board/(channel+'.png')))
            boards[-1][channel]={'dtype':str(data.dtype),'min':data.min(axis=(0,1)).tolist(),'max':data.max(axis=(0,1)).tolist(),'std':data.std(axis=(0,1)).tolist()}
    result={'boards':boards,'passed':all(b['passed'] for b in boards)}
    (OUT/'sd_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result)); assert result['passed']


def layout():
    """将已有参考与渲染缩略图排版为评审图；仅改变评审版式，不改资产像素。"""
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    sheet=Image.new('RGB',(1800,1300),(24,27,30)); draw=ImageDraw.Draw(sheet)
    tiles=[('REFERENCE',OUT/'reference.png'),('TRIPO / SEAT',OUT/'03_seat_detail.png'),('TRIPO / OVERVIEW',OUT/'02_final.png'),
        ('PREVIOUS / SAME LIGHT',OUT/'00_previous_tripo.png'),('PROCESS / SAME LIGHT',OUT/'01_process.png'),('APPEARANCE / SAME LIGHT',OUT/'02_final.png')]
    for k,(title,path) in enumerate(tiles):
        x=(k%3)*600; y=(k//3)*650
        draw.text((x+16,y+16),title,font=font,fill=(233,237,239))
        im=Image.open(path).convert('RGB'); im.thumbnail((584,584),Image.Resampling.LANCZOS)
        sheet.paste(im,(x+8+(584-im.width)//2,y+58+(584-im.height)//2))
    sheet.save(OUT/'reference_comparison.jpg',quality=94)
    sheet=Image.new('RGB',(1800,650),(24,27,30)); draw=ImageDraw.Draw(sheet)
    for k,(title,path) in enumerate([('HIGHLIGHT REFERENCE',OUT/'highlight_reference.png'),('BEFORE / GRAZING',OUT/'07_before_shading_fix.png'),('AFTER / GRAZING',OUT/'06_raking.png')]):
        x=k*600; draw.text((x+16,16),title,font=font,fill=(233,237,239))
        im=Image.open(path).convert('RGB'); im.thumbnail((584,584),Image.Resampling.LANCZOS); sheet.paste(im,(x+8+(584-im.width)//2,58+(584-im.height)//2))
    sheet.save(OUT/'highlight_comparison.jpg',quality=94)
    if (OUT/'12_final_diagnostic.png').is_file():
        sheet=Image.new('RGB',(1800,650),(24,27,30)); draw=ImageDraw.Draw(sheet)
        for k,(title,name) in enumerate([('CONSTANT ROUGH / FLAT NORMAL','10_flat_diagnostic'),('ROUGHNESS VARIATION ONLY','11_roughness_diagnostic'),('ROUGHNESS + MICRO NORMAL','12_final_diagnostic')]):
            x=k*600; draw.text((x+12,16),title,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20),fill=(233,237,239))
            im=Image.open(OUT/(name+'.png')).convert('RGB'); im.thumbnail((584,584),Image.Resampling.LANCZOS); sheet.paste(im,(x+8,58))
        sheet.save(OUT/'channel_isolation.jpg',quality=94)


if __name__=='__main__': check(); layout()
