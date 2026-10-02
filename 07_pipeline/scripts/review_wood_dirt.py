"""验证SD独立层归零、实际4K范围与渲染归零；生成评审拼版和1:1技术图裁片。"""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_dirt_20260930'
WORK=ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_dirt'
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')


def scalar(path):
    """输入灰度PNG，返回实际位深归一化数组；只读取，原图不修改。"""
    im=Image.open(path); a=np.asarray(im,dtype=np.float32)
    return a/(65535 if im.mode in ('I','I;16','I;16B') else 255)


def preview(path):
    """输入材质图，返回正确范围的评审副本；避免16位灰度被钳成全白。"""
    im=Image.open(path)
    if im.mode in ('I','I;16','I;16B'): im=Image.fromarray((np.asarray(im,dtype=np.uint16)//257).astype(np.uint8))
    return im.convert('RGB')


def main():
    """验证独立SD控制、归零画面与通道精度，然后拼合同光对照和裁片。"""
    # 仅改Blender颜色响应时复用已通过的原生SD检查，不重新渲染未改的SBSAR。
    reuse='--reuse-sd' in sys.argv
    records=json.loads((OUT/'sd_validation.json').read_text(encoding='utf-8'))['boards'] if reuse else {}
    for board in ([] if reuse else ['seat','back']):
        dest=WORK/('zero_'+board); dest.mkdir(exist_ok=True)
        command=[str(SD/'sbsrender.exe'),'render','--inputs',str(ROOT/'02_assets/materials/tripo_wood_dirt'/('wood_surface_dirt_'+board+'.sbsar')),
            '--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@10,10','--set-value','Dirt@0',
            '--engine','d3d11','--output-bit-depth','16','--no-report']
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/(board+'_zero.log')).write_text(done.stdout+done.stderr,encoding='utf-8'); assert done.returncode==0
        zero={name:float(scalar(dest/(name+'.png')).max()) for name in ['DirtMask','DirtHeight']}; assert all(v==0 for v in zero.values())
        stats={}
        for name in ['DirtMask','DirtHeight','DirtRoughness']:
            a=scalar(TEX/board/(name+'.png'))
            stats[name]={'size':list(a.shape),'min':float(a.min()),'max':float(a.max()),'std':float(a.std()),'fraction_gt_01':float((a>.1).mean())}
            assert a.shape==(4096,4096) and a.std()>0
        records[board]={'zero':zero,'actual_maps':stats}
    before=np.asarray(Image.open(OUT/'00_before_seat.png'),dtype=np.int16)
    after=np.asarray(Image.open(OUT/'06_zero_seat.png'),dtype=np.int16)
    delta=np.abs(before-after); assert float((delta>2).mean())<.001
    audit={'boards':records,'zero_render_8bit_difference':{'max':int(delta.max()),'mean':float(delta.mean()),'fraction_gt_2':float((delta>2).mean())}}
    (OUT/'sd_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25)
    pairs=[('seat_comparison.jpg',[('加脏渍前','00_before_seat.png'),('新增表面小脏渍','02_after_seat.png')],850),
        ('macro_comparison.jpg',[('加脏渍前／已有老化磨损','01_before_macro.png'),('新增细点与灰褐残留','03_after_macro.png')],1000)]
    if (OUT/'08_stain_after.png').is_file():
        pairs.append(('stain_comparison.jpg',[('脏渍关闭／原有木材','07_stain_before.png'),('小脏渍开启／局部近景','08_stain_after.png')],1000))
    for filename,items,size in pairs:
        canvas=Image.new('RGB',(size*2,size+60),(25,25,25)); draw=ImageDraw.Draw(canvas)
        for index,(label,file) in enumerate(items):
            canvas.paste(Image.open(OUT/file).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),(index*size,60))
            draw.text((index*size+16,14),label,font=font,fill='white')
        canvas.save(OUT/filename,quality=97)
    # 前左角残留区域，512px裁片约46mm宽，保留实际像素不放大。
    channels=['DirtMask','DirtColor','DirtRoughness','DirtHeight']
    canvas=Image.new('RGB',(2048,576),(25,25,25)); draw=ImageDraw.Draw(canvas)
    for index,name in enumerate(channels):
        crop=preview(TEX/'seat'/(name+'.png')).crop((670,620,1182,1132))
        canvas.paste(crop,(index*512,64)); draw.text((index*512+10,15),name+' / 1:1',font=font,fill='white')
    canvas.save(OUT/'map_100_percent.jpg',quality=97)
    print('SURFACE_DIRT_SD_VALIDATION '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
