"""从使用行为生成原创建模遮罩；输入为尺寸/随机种子，不输入任何参考照片。"""
from pathlib import Path
import hashlib, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'02_assets/materials/blackboard_age/inputs'
OUT.mkdir(parents=True,exist_ok=True)
W,H=2048,1024
FINAL=(4096,2048)
RNG=np.random.default_rng(190926)
u=np.linspace(0,1,W,dtype=np.float32)[None,:]
v=np.linspace(1,0,H,dtype=np.float32)[:,None]

def smooth(a,b,x):
    """输入上下界和数组；返回平滑的 0–1 过渡，避免新旧区域硬分界。"""
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def noise(cols,rows):
    """输入噪声格点数；返回插值后的低频场，不引入光照或照片信息。"""
    small=RNG.random((rows,cols),dtype=np.float32)
    return np.clip(np.asarray(Image.fromarray(small).resize((W,H),Image.Resampling.BICUBIC)),0,1)

def stroke_field(count):
    """输入擦拭次数；返回原尺寸板擦路径覆盖与纤维条纹，路径宽约 7–13 cm。"""
    coverage=np.zeros((H,W),np.float32)
    fibres=np.zeros_like(coverage)
    for index in range(count):
        # 从上中部活动范围采样；最下面约 25 cm 几乎不被板擦经过。
        cx,cz=RNG.uniform(.10,.90)*4.1438,RNG.uniform(.35,.88)*1.49
        angle=RNG.choice([0,math.pi/2,math.pi/5,-math.pi/5],p=[.22,.62,.08,.08])+RNG.normal(0,.12)
        length=RNG.uniform(.28,.78)
        width=RNG.uniform(.07,.13)
        dx,dz=math.cos(angle),math.sin(angle)
        bend=RNG.uniform(-.16,.16)
        xmin=max(0,int((cx-length-width)/4.1438*W));xmax=min(W,int((cx+length+width)/4.1438*W)+1)
        ymin=max(0,int((1-(cz+length+width)/1.49)*H));ymax=min(H,int((1-(cz-length-width)/1.49)*H)+1)
        xx=u[:,xmin:xmax]*4.1438-cx
        zz=v[ymin:ymax]*1.49-cz
        along=xx*dx+zz*dz
        across=-xx*dz+zz*dx-bend*(along/length)**2
        taper=np.exp(-(along/(length*.42))**4)
        band=np.exp(-(across/(width*.47))**2)
        pressure=band*taper
        phase=RNG.uniform(0,6)
        grain=.60+.25*np.sin(across*2800+phase)+.15*np.sin(across*4700+phase*.7)
        intensity=RNG.uniform(.35,.95)
        region=coverage[ymin:ymax,xmin:xmax]
        # 最近擦拭覆盖一部分旧层，保留手势交错和软边，不堆成均匀噪点。
        coverage[ymin:ymax,xmin:xmax]=region*(1-pressure*.40)+pressure*intensity*.40
        old=fibres[ymin:ymax,xmin:xmax]
        fibres[ymin:ymax,xmin:xmax]=old*(1-pressure*.40)+pressure*grain*intensity*.40
    return coverage,fibres

def save(name,array):
    """输入名称和 0–1 灰度数组；输出 16 位无光照数据贴图及文件记录。"""
    values=np.clip(np.asarray(Image.fromarray(array.astype(np.float32)).resize(FINAL,Image.Resampling.BICUBIC)),0,1)
    path=OUT/(name+'.png')
    Image.fromarray(np.round(values*65535).astype(np.uint16)).save(path)
    return {'name':name,'path':str(path),'size':list(FINAL),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bottom_mean':float(values[int(FINAL[1]*.84):].mean()),'upper_mean':float(values[int(FINAL[1]*.13):int(FINAL[1]*.65)].mean())}

cloud=noise(11,7)
fine=noise(130,58)
boundary=.225+.040*(noise(8,3)-.5)
use=smooth(boundary-.035,boundary+.13,v)*(1-.10*smooth(.91,1,v))
use*=smooth(.006,.035,u)*smooth(.006,.035,1-u)
sweeps,fibres=stroke_field(380)
wear=use*np.clip(.28+.42*cloud+.38*sweeps,0,1)

# 固着粉笔灰偏灰白；低部只留少量空气沉积，边槽积粉限制在几毫米。
embedded=use*np.clip(.22+.60*cloud+.12*fine,0,1)
fresh=use*np.clip(.12+.24*cloud+.48*sweeps+.16*fibres,0,1)
sun=np.clip((1-u)**1.4*(.35+.65*v)*(.72+.28*noise(5,4)),0,1)
edge=np.exp(-v/.007)*(.20+.80*noise(45,3))*.45

# 原创模糊断笔只记录残留方向；不复制参考图文字，也不生成可读的新板书。
ghost_image=Image.new('L',(W,H),0)
draw=ImageDraw.Draw(ghost_image)
for row in range(4):
    z=.78-row*.135
    for col in range(25):
        if RNG.random()<.32: continue
        x=.07+col*.034+RNG.normal(0,.005)
        y=1-z+RNG.normal(0,.006)
        for part in range(int(RNG.integers(1,4))):
            dx,dy=RNG.uniform(.006,.017),RNG.uniform(.020,.040)
            points=[(int(x*W),int(y*H)),(int((x+dx*.4)*W),int((y+dy*.45)*H)),
                    (int((x+dx)*W),int((y+dy)*H))]
            draw.line(points,fill=int(RNG.integers(80,180)),width=int(RNG.integers(1,3)))
            x+=.004
ghost=np.asarray(ghost_image.filter(ImageFilter.GaussianBlur(.85)),dtype=np.float32)/255
ghost*=use*(.15+.85*noise(145,90))*(1-.7*sweeps)

# 手掌接触在书写区少量出现，影响磨亮，不加大面积油污或生锈。
soil=use*np.maximum(noise(21,10)-.46,0)*.9
records=[save(name,array) for name,array in [('UseMask',use),('Abrasion',wear),('EmbeddedChalk',embedded),
          ('EraserPasses',fresh),('SunFade',sun),('GhostWriting',ghost),('EdgeDust',edge),('TouchSoil',soil)]]
(OUT/'manifest.json').write_text(json.dumps({'method':'Original deterministic physical-scale eraser trajectories and spatial masks',
 'seed':190926,'surface_metres':[4.143805,1.49],'image_top_is_board_top':True,'reference_pixels_used':False,'maps':records},indent=2),encoding='utf-8')
print('BLACKBOARD_MASKS_READY',len(records),flush=True)
