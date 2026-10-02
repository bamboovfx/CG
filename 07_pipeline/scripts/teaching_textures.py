"""原创程序材质，不是扫描。生成黑板擦痕、纸张、布封皮与细微表面；seed 固定可复现。"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import json, hashlib
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'02_assets/textures/authored/teaching_rebuild';OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(20260911)
N=2048

def cloud(w,h,size=64):
    """输入输出尺寸和噪声网格尺寸，返回双三次放大的低频连续随机场。"""
    a=Image.fromarray(rng.integers(0,256,(size,size),dtype=np.uint8))
    return np.asarray(a.resize((w,h),Image.Resampling.BICUBIC),dtype=np.float32)/255-.5

def save(name,a):
    """输入线性0-1灰度或显示RGB数组，输出8位PNG工作图并返回路径。"""
    p=OUT/(name+'.png');Image.fromarray(np.uint8(np.clip(a,0,1)*255)).save(p);return p

def family(name,color,rough=.65):
    """输入材质族名称/显示颜色/粗糙度，输出共享2K三通道；微表面幅度由着色器控制。"""
    n=cloud(N,N,72)*.025+cloud(N,N,310)*.012+rng.normal(0,.003,(N,N))
    yy,xx=np.mgrid[:N,:N]
    if name=='cloth':n+=.008*(np.sin(xx*2.2)+np.sin(yy*2.0))
    if name=='paper':n+=.003*np.sin(xx*.8+yy*.12)
    save(name+'_color',np.array(color)[None,None,:]+n[:,:,None])
    save(name+'_rough',rough+n*2)
    save(name+'_height',.5+n*4)

for args in [('paper',(.79,.756,.657),.8),('cloth',(.25,.31,.27),.77),('ivory',(.68,.675,.606),.44),('metal',(.43,.455,.445),.39),('dark',(.075,.074,.067),.69),('felt',(.16,.19,.17),.91)]:family(*args)
# The blackboard map follows a full board-sized UV island: no obvious repeating tiles.
w,h=4096,2048
Y,X=np.mgrid[:h,:w];u=X/w;v=Y/h
wipe=np.zeros((h,w),np.float32)
for i in range(65):
    x,y=rng.uniform(0,1),rng.uniform(.04,.98);sx,sy=rng.uniform(.035,.20),rng.uniform(.008,.028)
    angle=rng.uniform(-.14,.14);dy=v-y-angle*(u-x)
    wipe+=rng.uniform(.010,.033)*np.exp(-((u-x)/sx)**2-(dy/sy)**2)
# Lower edge gathers a faint dust band; broad wipes stay subordinate to the reference's empty board.
dust=.025*np.exp(-((1-v)/.055)**2)*(cloud(w,h,140)+.65)
fine=cloud(w,h,340)*.006+rng.normal(0,.0015,(h,w))
base=np.array([.058,.186,.127])[None,None,:]
save('blackboard_color',base+(wipe+dust+fine)[:,:,None]*np.array([.72,.81,.67]))
save('blackboard_rough',.69+wipe*1.4+fine*2)
save('blackboard_height',.5+fine*7+wipe*.6)
# Each notice has intentionally nonsemantic gray rule fragments: no invented quotation from the film.
for i in range(5):
    a=np.asarray(Image.open(OUT/'paper_color.png')).copy()
    a=np.clip(a.astype(float)+i*1.1,0,255).astype('uint8');im=Image.fromarray(a);d=ImageDraw.Draw(im)
    c=(95+i*4,101+i*3,90+i*4)
    if i%2==0:
        for col in range(6):
            x=470+col*205
            for row in range(16):
                y=360+row*76
                if rng.random()>.24:d.line((x,y,x+int(rng.integers(20,75)),y),fill=c,width=4)
    else:
        for row in range(18):
            y=400+row*66
            for j in range(int(rng.integers(5,11))):
                x=340+j*130;d.line((x,y,x+int(rng.integers(25,85)),y),fill=c,width=3)
        d.rectangle((290,290,1740,1660),outline=(146,145,127),width=3)
    im=im.filter(ImageFilter.GaussianBlur(1.2));im.save(OUT/f'notice_{i:02}_color.png')
files=[]
for p in OUT.glob('*.png'):
    files.append({'file':str(p.relative_to(ROOT)),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':'original authored procedural; not a scan','seed':20260911})
(OUT/'manifest.json').write_text(json.dumps({'date':'2026-09-11','method':'NumPy/Pillow authored surface maps; colors are sRGB; rough/height Non-Color; no AI generation, no third-party pixels','files':files},indent=2),encoding='utf-8')
print('Authored maps:',len(files))
