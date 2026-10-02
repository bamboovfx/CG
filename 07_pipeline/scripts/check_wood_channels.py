"""校验SD效果归零后的五通道，并生成原始渲染的分层评审拼图。

输入：本轮SD归档、已完成的Blender同光渲染。
输出：五通道像素差验证与分层拼图；不改变素材和渲染图。
"""
from pathlib import Path
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'07_pipeline/cache/wood_layers_20260930/zero_controls'
OUT=ROOT/'06_review/wood_layers_20260930'


def main():
    """输入本轮清单，渲染三参数归零，比较五通道并输出带标题的四阶段拼图。"""
    WORK.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'02_assets/textures/generated/wood_layers/manifest.json').read_text(encoding='utf-8'))
    cmd=list(manifest['commands'][1])
    cmd[cmd.index('--output-path')+1]=str(WORK)
    cmd+=['--set-value','Scratches@0','--set-value','Age@0','--set-value','Wear@0']
    done=subprocess.run(cmd,capture_output=True,text=True)
    (WORK/'render_result.txt').write_text(done.stdout+done.stderr,encoding='utf-8')
    if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-2000:])
    differences={}
    for channel in ['BaseColor','Roughness','Metallic','Normal','AO']:
        a=np.asarray(Image.open(WORK/(channel+'.png'))).astype(np.int32)
        b=np.asarray(Image.open(WORK/('Process_'+channel+'.png'))).astype(np.int32)
        differences[channel]=int(np.max(np.abs(a-b)))
    audit={'max_pixel_difference':differences,'passed':all(v==0 for v in differences.values()),'source_sha256':manifest['source_sha256'],'parameters':{'Scratches':0,'Age':0,'Wear':0}}
    (OUT/'zero_control_validation.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    if not audit['passed']: raise RuntimeError('Appearance disabled does not match process channels')
    # 只为评审并列显示原始渲染，不修改参考照片或材质输出。
    canvas=Image.new('RGB',(1240,1320),(22,26,31)); draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    stages=[('01_process','01  PROCESS'),('02_scratches','02  + SCRATCHES'),('03_age','03  + AGE'),('04_appearance','04  + EDGE WEAR')]
    for index,(name,label) in enumerate(stages):
        x=20+(index%2)*610; y=20+(index//2)*650
        im=Image.open(OUT/(name+'.png')).convert('RGB').resize((600,600),Image.Resampling.LANCZOS)
        canvas.paste(im,(x,y+38)); draw.text((x+8,y+4),label,font=font,fill=(229,233,239))
    canvas.save(OUT/'layer_comparison.jpg',quality=94)
    print(json.dumps(audit))


if __name__=='__main__':
    main()
