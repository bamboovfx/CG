"""Author deterministic 2K material maps at a documented 0.25 m tile size; no external texture copying."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
import json,hashlib
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'02_assets/textures/authored/equipment_rebuild';OUT.mkdir(parents=True,exist_ok=True)
N=2048;rng=np.random.default_rng(91126)
# Different scales separate manufacturing microtexture from broad ageing; amplitudes remain restrained.
def field(size,blur=0):
    """Return normalized low-frequency random field from input seed-grid size and blur radius."""
    im=Image.fromarray(np.uint8(rng.random((size,size))*255)).resize((N,N),Image.Resampling.BICUBIC)
    if blur: im=im.filter(ImageFilter.GaussianBlur(blur))
    a=np.asarray(im,dtype=np.float32)/255
    return (a-.5)
low=field(12,12);mid=field(170,1);fine=field(1200,.35)
families={'enamel':((178,171,148),.47,.035),'abs':((100,105,93),.48,.055),'glass':((68,77,68),.16,.005),'metal':((165,167,158),.33,.02),'rubber':((28,30,27),.7,.04),'paper':((220,216,194),.76,.018),'dark':((37,39,35),.53,.02)}
manifest=[]
for family,(rgb,rough,amp) in families.items():
    variation=low*.014+mid*.016+fine*amp
    col=np.clip(np.array(rgb)[None,None,:]*(1+variation[:,:,None]),0,255).astype('uint8')
    roughness=np.clip(rough+low*.018+mid*.028+fine*amp,0,1)
    height=np.clip(.5+fine*.22+mid*.06,0,1)
    if family=='metal':
        # Directional rolling marks have a physical orientation; unlike isotropic salt-and-pepper noise.
        hair=field(1000,0).mean(axis=1)[:,None];roughness+=hair*.3
    for channel,a in [('color',col),('roughness',np.uint8(roughness*255)),('height',np.uint8(height*255))]:
        p=OUT/f'{family}_{channel}_2k.png';Image.fromarray(a).save(p)
        manifest.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'resolution':[N,N],'channel':channel,'color_space':'sRGB' if channel=='color' else 'Non-Color','tile_metres':.25,'source':'Original deterministic authored manufacturing microtexture, seed 91126; not scanned','license':'Project authored','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
# Clock face print, aligned in local X/Z with true 2048 px dial artwork and no invented maker.
im=Image.new('RGB',(N,N),(221,217,194));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',170)
import math
for k in range(60):
 a=k*math.tau/60;r0=840 if k%5==0 else 880;r1=929
 d.line([(1024+math.sin(a)*r0,1024-math.cos(a)*r0),(1024+math.sin(a)*r1,1024-math.cos(a)*r1)],fill=(29,32,28),width=18 if k%5==0 else 6)
for k in range(1,13):
 a=k*math.tau/12;p=(1024+math.sin(a)*700,1024-math.cos(a)*700)
 d.text(p,str(k),font=font,fill=(32,34,30),anchor='mm')
p=OUT/'clock_dial_color_2k.png';im.save(p);manifest.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'resolution':[N,N],'channel':'color','color_space':'sRGB','mapping':'Entire 0.316 m diameter dial in UV 0..1','source':'Original printed clock face, Arial system font; no brand','license':'Project authored','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'texture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Authored',len(manifest),'maps')
# Full-door ageing maps: edge accumulation and hand-polished pull zone, not homogeneous noise.
y,x=np.mgrid[0:N,0:N].astype(np.float32);x/=N-1;y/=N-1
edge=np.exp(-np.minimum(np.minimum(x,1-x),np.minimum(y,1-y))*90)
hand=np.exp(-(((x-.82)/.10)**2+((y-.5)/.11)**2))
bottom=np.exp(-(1-y)*20)*(0.4+0.6*(np.sin(x*14)**2))
wear=edge*.075+bottom*.065+hand*.032+low*.015
col=np.clip(np.array((178,171,148))[None,None,:]*(1-wear[:,:,None]),0,255).astype('uint8')
rr=np.clip(.47+edge*.07+bottom*.055-hand*.10+mid*.025,0,1)
for channel,a in [('color',col),('roughness',np.uint8(rr*255))]:
 p=OUT/f'cabinet_door_{channel}_2k.png';Image.fromarray(a).save(p)
 manifest.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'resolution':[N,N],'channel':channel,'color_space':'sRGB' if channel=='color' else 'Non-Color','mapping':'One image across 0.53 x 1.112 m door face; hand zone and edge grime','source':'Original authored function, not scanned','license':'Project authored','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'texture_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
