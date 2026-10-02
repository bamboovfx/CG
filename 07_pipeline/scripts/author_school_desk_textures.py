"""课桌专用 2K 材质图：按实际 UV 尺度布置磨损，不烘焙光照。

输入：CC0 plywood 扫描；输出：饰面、胶合板边、烤漆管、桌肚、锈蚀横撑、脚套的 PBR 图。
磨损是参考驱动的人工程序绘制，并非原物扫描或照片投射。
"""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'02_assets/textures/authored/school_desk/2k'
OUT.mkdir(parents=True, exist_ok=True)
N = 2048
rng = np.random.default_rng(3087)
Y, X = np.mgrid[0:N, 0:N].astype(np.float32)/(N-1)


def noise(w, h):
    """输入横纵噪声格数；输出 2K 浮点平滑场，用格数控制物理尺度。"""
    a = rng.random((h, w), dtype=np.float32)
    return np.asarray(Image.fromarray(a).resize((N, N), Image.Resampling.BICUBIC))


def save_set(name, color, rough, metal, height):
    """输入材质名与四个线性/颜色数组；保存 sRGB 色图及 Non-Color 标量图。"""
    for channel, a in [('BaseColor',color),('Roughness',rough),('Metallic',metal),('Height',height)]:
        if np.isscalar(a):
            a = np.full((N, N), a)
        im = Image.fromarray((np.clip(a, 0, 1)*255+.5).astype(np.uint8))
        im.save(OUT/f'{name}_{channel}.png')
    print('TEXTURE_READY', name, flush=True)


def stroke_mask(count, length, width, vertical=False):
    """输入划痕数量、像素长度、宽度和方向；输出稀疏非重复划痕遮罩。"""
    im = Image.new('L',(N,N)); d = ImageDraw.Draw(im)
    for _ in range(count):
        x,y = rng.integers(0,N,2); l = int(rng.uniform(.1,1)*length)
        dx,dy = (int(rng.normal(0,4)),l) if vertical else (l,int(rng.normal(0,5)))
        d.line((int(x),int(y),int(x+dx),int(y+dy)),fill=int(rng.uniform(40,220)),width=width)
    return np.asarray(im,dtype=np.float32)/255


def painted(name, kind, variant=0, oxidation_age=.72):
    """输入烤漆类别、变体和独立氧化年龄；输出分离的磨损/锈蚀遮罩及合成 PBR。"""
    # 管 UV 横向是一周约 8 cm，纵向是约 1.4 m 弧长；面板另用 50×10 cm 尺度。
    tube = kind in ['tube','brace','hook']
    broad = noise(10,55) if tube else noise(55,14)
    mid = noise(65,700) if tube else noise(800,180)
    fine = noise(480,1700)
    if kind == 'tube':
        ends = np.exp(-Y*23)+np.exp(-(1-Y)*23)
        threshold = .79-.21*ends-.06*np.exp(-((Y-.085)/.018)**2)
    elif kind == 'brace':
        threshold = .19
    elif kind == 'hook':
        threshold = .64
    else:
        # 桌肚的主要破损集中在编号、中央擦碰和下沿，保持大块漆面完整。
        patch = np.exp(-((X-.29)/.065)**2-((Y-.56)/.13)**2)
        patch += .8*np.exp(-((X-.55)/.028)**2-((Y-.70)/.16)**2)
        threshold = .89-.25*patch-.11*np.exp(-(1-Y)*24)
    field = broad*.72+mid*.23+fine*.05
    chips = np.clip((field-threshold)*70,0,1)
    halo = np.clip((field-threshold+.033)*19,0,1)
    # 氧化使用独立场，掉漆不等同于生锈。常擦碰处允许残留裸钢反射。
    oxidation = noise(33,270) if tube else noise(210,50)
    rust = np.clip((oxidation-(.65-oxidation_age*.48))*5,0,1)
    if kind=='brace': rust=np.clip(.96+(oxidation-.5)*.20,.92,1)
    rustgrain=noise(580,1500)
    rustcol = np.stack([.15+oxidation*.19+rustgrain*.07,
                        .085+oxidation*.10+rustgrain*.045,
                        .040+oxidation*.055+rustgrain*.028],axis=-1)
    bare_steel=np.stack([.49+mid*.11,.51+mid*.11,.51+mid*.10],axis=-1)
    exposed=bare_steel*(1-rust[...,None])+rustcol*rust[...,None]
    paint = np.array([.62,.62,.555])+((broad-.5)*.055+(fine-.5)*.023)[...,None]
    paint -= halo[...,None]*np.array([.04,.065,.085])
    col = paint*(1-chips[...,None])+exposed*chips[...,None]
    scratches = stroke_mask(120 if tube else 38,48 if tube else 95,1,vertical=tube)
    grime=noise(8,85) if tube else noise(50,10)
    dirt=np.clip((grime-.55)*1.7,0,.4)*(1-chips*.65)
    col -= scratches[...,None]*.065+dirt[...,None]*np.array([.09,.08,.055])
    # 局部擦亮改变 Roughness，锈层孔蚀改变 Height；不让所有通道复制同一噪声。
    polished=np.clip((noise(15,95) if tube else noise(105,20))-.58,0,1)*.35
    paint_rough=.51+noise(45,170)*.10-polished+dirt*.12
    rust_rough=.78+rustgrain*.14
    steel_rough=.27+mid*.18
    rough=paint_rough*(1-chips)+chips*(steel_rough*(1-rust)+rust_rough*rust)
    lip=np.exp(-((field-threshold+.008)/.013)**2)*(1-chips)
    height=.57-chips*.27+lip*.055+(fine-.5)*.035+chips*rust*(rustgrain-.5)*.21-scratches*.045
    save_set(name,col,rough,chips*(1-rust),height)
    for channel,mask in [('WearMask',chips),('RustMask',chips*rust),('DirtMask',dirt)]:
        Image.fromarray((np.clip(mask,0,1)*255).astype(np.uint8)).save(OUT/f'{name}_{channel}.png')
    return col, chips, height


# 色图只借用扫描的纤维分布；饰面色调、划伤和磨白独立绘制。
src = ROOT/'02_assets/textures/polyhaven/plywood/4k/plywood_diff_4k.jpg'
wood = np.asarray(Image.open(src).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),dtype=np.float32)/255
grain = wood.mean(axis=2); grain = (grain-grain.mean())*.88
longgrain = noise(20,1200)-.5
cloud = noise(13,13)
scratch = stroke_mask(630,260,1)+stroke_mask(35,65,2)
wear = np.clip((noise(45,45)-.59)*2,0,.30)
top = np.array([.34,.315,.30])+grain[...,None]*1.35+longgrain[...,None]*.11
top += wear[...,None]*.16+scratch[...,None]*.13
save_set('laminate_top',top,.52+cloud*.12+wear*.25+scratch*.10,0,.5+grain*.03-scratch*.026)

# 胶合板边：横轴为周长，纵轴为厚度；薄层和崩口有不同的粗糙度与高度。
layer = np.sin(Y*2*np.pi*7+noise(12,5)*.42)
fiber = noise(95,620)
edgefield = noise(220,9)*.65+noise(1200,40)*.35
chip = np.clip((edgefield-(.85-.28*np.exp(-Y*18)-.08*np.exp(-(1-Y)*18)))*22,0,1)
# 胶层不是规则正弦条纹：单板厚度略有差异，边界随木纤维轻微起伏。
# 保存随机状态，单独修改板边不会重新打乱已评审过的金属磨损位置。
metal_seed_state=rng.bit_generator.state
warp=(noise(48,3)-.5)*.010+(noise(210,4)-.5)*.002
bounds=[.0,.14,.295,.43,.575,.715,.87,1.0]
edge=np.zeros((N,N,3),dtype=np.float32)
glue=np.zeros((N,N),dtype=np.float32)
for i,(a,b) in enumerate(zip(bounds,bounds[1:])):
    slab=((Y+warp>=a)&(Y+warp<b)).astype(np.float32)
    tone=[-.008,.016,-.019,.008,-.012,.020,-.007][i]
    grain_edge=noise(105,1500) if i%2==0 else noise(950,90)
    veneer=np.array([.385,.285,.175])+tone+(grain_edge[...,None]-.5)*.065
    edge+=slab[...,None]*veneer
    if i:glue=np.maximum(glue,np.exp(-((Y+warp-a)/.003)**2))
edge[Y+warp>=1]=[.40,.30,.19];edge[Y+warp<0]=[.40,.30,.19]
edge-=glue[...,None]*np.array([.11,.09,.055])
rubbed=np.clip((noise(240,8)-.48)*1.8,0,.75)*np.exp(-Y*8)
bare=np.array([.58,.46,.29])+(fiber[...,None]-.5)*.12
exposed=np.maximum(chip,rubbed)
edge=edge*(1-exposed[...,None])+bare*exposed[...,None]
stain=np.clip((noise(50,9)-.61)*1.2,0,.26)
edge-=stain[...,None]*.18
save_set('plywood_edge',edge,.54+exposed*.22+stain*.14,0,.55-chip*.20-glue*.055+(fiber-.5)*.055)
rng.bit_generator.state=metal_seed_state
painted('frame_left','tube')
painted('frame_right','tube',1)
painted('lower_brace','brace')
painted('hardware','hook')
tray, chips, height = painted('tray','tray')

# 正面独有的残留标记；文字是重绘的淡化资产标识，不冒充可辨识的原物文字。
mark = Image.new('L',(N,N)); d = ImageDraw.Draw(mark)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',130)
d.text((290,880),'3',font=font,fill=130)
d.ellipse((970,825,1043,1170),outline=100,width=7)
d.line((991,1150,960,1290),fill=110,width=7)
d.rounded_rectangle((1690,790,1830,1150),radius=15,outline=80,width=10)
d.line((1695,900,1825,900),fill=75,width=8)
markarr = np.asarray(mark,dtype=np.float32)/255
markarr *= np.clip((noise(340,110)-.26)*2,0,1)
tray -= markarr[...,None]*.24
# 正面继承相同底层状态；编号只影响漆面颜色，不改变裸钢的金属属性。
tray_rough=np.asarray(Image.open(OUT/'tray_Roughness.png'),dtype=np.float32)/255
tray_metal=np.asarray(Image.open(OUT/'tray_Metallic.png'),dtype=np.float32)/255
save_set('tray_front',tray,tray_rough,tray_metal,height)
for channel in ['WearMask','RustMask','DirtMask']:
    Image.open(OUT/f'tray_{channel}.png').save(OUT/f'tray_front_{channel}.png')

# 黄化聚合物脚套：地面附近的脏污集中在 UV 底部。
fine = noise(500,500)
dirt = np.exp(-(1-Y)*9)*(.25+noise(34,35)*.5)
rubber = np.array([.70,.675,.46])+(fine[...,None]-.5)*.025-dirt[...,None]*.31
ground_grime=np.clip((noise(18,15)-.49)*2.3,0,.65)*np.exp(-(1-Y)*4.5)
rubber=rubber*(1-ground_grime[...,None])+np.array([.24,.23,.18])*ground_grime[...,None]
save_set('foot_caps',rubber,.62+fine*.15,0,.5+(fine-.5)*.10)

files = [{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
          'size':[N,N], 'colorspace':'sRGB' if 'BaseColor' in p.name else 'Non-Color'} for p in sorted(OUT.glob('*.png'))]
manifest = {'asset':'school_desk','kind':'authored_reference_driven_PBR','seed':3087,
            'source':{'url':'https://polyhaven.com/a/plywood','license':'CC0','path':str(src.relative_to(ROOT)),
                      'sha256':hashlib.sha256(src.read_bytes()).hexdigest()},
            'reference':'https://aita.ocnk.net/product/3087','physical_dimensions_m':[.60,.40,.67],
            'mapping':{'top':'.60 x .40 m','edge':'2.0 m perimeter x .018 m thickness',
                       'frame':'circumference x normalized path length','tray_front':'.47 x .10 m'},
            'notes':'No baked lighting. Wear, oxidation and dirt have separate masks. PBR channels use distinct physical responses. Wear and inferred markings are authored; not a scan of the reference desk.',
            'method_references':[{'url':'https://tsvetelina-valkanova.artstation.com/projects/mN3JY','used':'Artist description of separate rust, rough metal and paint layers; no textures copied'},
                                 {'url':'https://andreariccardi.artstation.com/projects/QzmB2B','used':'Artist description of independently controlled age and wear; no textures copied'}],
            'files':files}
(OUT.parent/'texture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
