"""按最终Blender强度导出SD PBR，验证归零、源文件和真实细节，再组合评审图。"""
from pathlib import Path
import subprocess
import hashlib
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
TEX=ROOT/'02_assets/textures/generated/tripo_wood_detail'
OUT=ROOT/'06_review/tripo_wood_detail_20260930'
WORK=ROOT/'07_pipeline/cache/tripo_wood_detail_20260930'
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
manifest=json.loads((TEX/'manifest.json').read_text(encoding='utf-8'))
PARAMS={'Scratches':.95,'Age':1.0,'Wear':.95}


def run(board,dest,power,params):
    """输入板、目标目录、输出幂次和参数，执行可追溯渲染；不重烹资源。"""
    dest.mkdir(parents=True,exist_ok=True)
    command=[str(SD/'sbsrender.exe'),'render','--inputs',str(ROOT/board['source']).replace('.sbs','.sbsar'),
        '--output-path',str(dest),'--output-name','{outputNodeName}','--set-value',f'$outputsize@{power},{power}',
        '--engine','d3d11','--output-bit-depth','16','--no-report']
    for k,v in params.items(): command+=['--set-value',f'{k}@{v}']
    done=subprocess.run(command,capture_output=True,text=True)
    (WORK/(board['board']+'_'+dest.name+'.log')).write_text(done.stdout+done.stderr,encoding='utf-8')
    assert done.returncode==0,(done.stdout+done.stderr)[-2000:]


def stats(path):
    """输入实际灰度PNG，返回归一化数值范围与方差，不改动图像。"""
    im=Image.open(path); a=np.asarray(im,dtype=np.float32)
    a/=65535 if im.mode in ('I','I;16','I;16B') else 255
    return {'pixels':list(im.size),'min':float(a.min()),'max':float(a.max()),'std':float(a.std())}


def main():
    """保存参数化导出、SD归零与工艺保护结果；仅把已渲染图组成评审版式。"""
    results=[]
    for board in manifest['boards']:
        # 重渲同一个归档，让五通道对应最终强度；Raw图保持原来的扫描结构。
        run(board,TEX/board['board'],12,PARAMS)
        dest=WORK/('zero_'+board['board']); run(board,dest,10,{k:0 for k in PARAMS})
        zero_height=stats(dest/'EffectHeight.png'); metallic=stats(dest/'Metallic.png')
        assert zero_height['std']<1e-6 and abs(zero_height['min']-.5)<2/65535
        assert metallic['max']==0
        detail={name:stats(TEX/board['board']/('Raw_'+name+'.png')) for name in ('AgeMask','AgeHeight','WearHeight','ScratchCore','ScratchLip')}
        assert all(d['pixels']==[4096,4096] and d['std']>0 for d in detail.values())
        results.append({'board':board['board'],'zero_height':zero_height,'metallic':metallic,'raw_detail':detail})
    protected={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['protected_process_files'].items()}
    assert all(protected.values())
    before=np.asarray(Image.open(OUT/'01_process_before.png'),dtype=np.int16)
    after=np.asarray(Image.open(OUT/'02_process_after.png'),dtype=np.int16)
    delta=np.abs(before-after)
    assert float((delta>2).mean())<.001
    audit={'boards':results,'native_export_parameters':PARAMS,'process_files_unchanged':protected,
        'process_render_8bit_difference':{'max':int(delta.max()),'mean':float(delta.mean()),'fraction_over_2':float((delta>2).mean())}}
    manifest['native_export_parameters']=PARAMS
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'sd_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
    pairs=[('appearance_comparison.jpg',[('上一版／被否定','00_rejected_seat.png'),('扫描细节表现层','03_detail_seat.png')]),
        ('macro_comparison.jpg',[('上一版／规则条带','00_rejected_macro.png'),('新版／接触区细节','06_contact_macro.png')]),
        ('effect_isolation.jpg',[('工艺层','02_process_after.png'),('老化独立','09_age_only.png'),('磨损独立','10_wear_only.png')])]
    for filename,items in pairs:
        size=700 if len(items)==2 else 560
        canvas=Image.new('RGB',(len(items)*size,size+58),(25,25,25)); draw=ImageDraw.Draw(canvas)
        for index,(label,name) in enumerate(items):
            im=Image.open(OUT/name).convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
            canvas.paste(im,(index*size,58)); draw.text((index*size+15,12),label,font=font,fill='white')
        canvas.save(OUT/filename,quality=96)
    print('SD_DETAIL_VALIDATION '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
