"""制作可复用的 2K 工作贴图。输入扫描源；输出衍生图、程序化图文及来源清单。"""
from pathlib import Path
import hashlib
import json
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '02_assets/textures/authored/classroom/2k'
OUT.mkdir(parents=True, exist_ok=True)
N = 2048
rng = np.random.default_rng(908)
records = []

def record(path, source, channel):
    """输入文件、来源和通道；把尺寸和哈希加入依赖记录，无返回值。"""
    records.append(dict(path=path.relative_to(ROOT).as_posix(), source=source,
                        channel=channel, size=list(Image.open(path).size),
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

def save(array, name, channel):
    """输入 0–1 数组与命名；保存 8bit PNG 并记录原创程序化来源，返回路径。"""
    path = OUT / f'{name}_{channel}_2k.png'
    Image.fromarray(np.uint8(np.clip(array, 0, 1)*255)).save(path)
    record(path, 'Original deterministic procedural texture; seed 908; not a scan or AI image', channel)
    return path

# 保留 4K 源，工作材质统一引用 2K 衍生文件。
for asset in ['plywood', 'old_wooden_floor_03']:
    for source in (ROOT/f'02_assets/textures/polyhaven/{asset}/4k').glob('*'):
        if source.suffix.lower() not in ['.png', '.jpg']: continue
        target = OUT / source.name.replace('4k', '2k')
        Image.open(source).resize((N, N), Image.Resampling.LANCZOS).save(target)
        record(target, source.relative_to(ROOT).as_posix()+'; Poly Haven CC0; Lanczos downsample',
               'normal' if 'nor_gl' in source.name else 'roughness' if 'rough' in source.name else 'color')

# 中性微表面按材质族共享；用标量起伏生成 OpenGL 法线，幅度保持克制。
small = rng.random((256, 256)).astype(np.float32)
coarse = np.asarray(Image.fromarray(np.uint8(small*255)).resize((N,N), Image.Resampling.BICUBIC), dtype=np.float32)/255
fine = rng.normal(0,.045,(N,N)).astype(np.float32)
for name, rough, strength in [('paint',.43,.35),('metal',.3,.2),('rubber',.76,.8),
                               ('paper',.87,.45),('glass',.08,.025),('plastic',.36,.25),
                               ('chalkboard',.88,.24),('wood_edge',.54,.2),('print',.52,.12)]:
    height = np.clip(coarse*.25+fine+.4,0,1)
    if name=='wood_edge':
        height = .48+.06*np.sin(np.arange(N)[:,None]*.23)+fine*.3+np.zeros((1,N))
    if name=='metal':
        height += rng.normal(0,.025,(1,N))
    grad_y, grad_x = np.gradient(height)
    normal = np.stack((-grad_x*strength, grad_y*strength, np.ones_like(height)),axis=-1)
    normal /= np.linalg.norm(normal,axis=-1,keepdims=True)
    save(normal*.5+.5,name,'normal')
    save(np.clip(rough+(height-.5)*(.025 if name=='glass' else .16),.015,.98),name,'roughness')
    save(np.repeat((.88+(height-.5)*.12)[...,None],3,axis=-1),name,'color')

# 印刷内容为本项目原创的日式教室道具，不冒充原片可辨文字。
font_path = 'C:/Windows/Fonts/msyh.ttc'
if not Path(font_path).exists(): font_path='C:/Windows/Fonts/arial.ttf'
def font(size):
    """输入字号；返回系统字体，仅用于把文字栅格化到原创贴图。"""
    return ImageFont.truetype(font_path,size)

for index,title in enumerate(['今週の予定','図書だより','清掃当番','学校からのお知らせ','時間割']):
    base=np.repeat((.93+fine*.18)[...,None],3,axis=-1)*np.array([1,.978,.91])
    im=Image.fromarray(np.uint8(np.clip(base,0,1)*255));d=ImageDraw.Draw(im)
    ink=(65,75,68);accent=[(75,106,104),(125,83,65),(81,98,75),(118,81,76),(64,84,109)][index]
    d.rectangle((125,140,1923,168),fill=accent)
    d.text((145,225),title,font=font(148),fill=accent)
    d.text((150,420),'9月  /  CLASSROOM  2–A',font=font(50),fill=ink)
    if index in [0,2,4]:
        for y in range(580,1720,180): d.line((145,y,1900,y),fill=(145,149,133),width=3)
        for x in range(145,1901,350): d.line((x,580,x,1660),fill=(145,149,133),width=3)
        for row in range(6):
            for col in range(5):
                d.text((170+col*350,615+row*180),['国語','算数','理科','音楽','図工'][(row+col+index)%5],font=font(56),fill=ink)
    else:
        lines=['みんなで使う教室を大切に。','本を読んだら、元の場所へ。','窓を開けて、空気を入れかえます。','放課後は忘れ物を確認しましょう。']
        for row in range(8):d.text((155,600+row*108),lines[row%4],font=font(58),fill=ink)
        d.rectangle((155,1520,1880,1700),outline=accent,width=4)
        d.text((205,1570),'係からの連絡  /  お願い',font=font(65),fill=accent)
    d.text((150,1840),'学級掲示  •  09 / 08',font=font(42),fill=(115,112,99))
    path=OUT/f'notice_{index:02d}_color_2k.png';im.save(path)
    record(path,'Original typeset classroom prop, not a transcription of film text','color')

# 黑板擦拭痕迹有方向性，色差来自颜料/粉笔残留，不包含模拟光照。
im=Image.new('L',(N,N),12);d=ImageDraw.Draw(im)
for i in range(350):
    x=int(rng.integers(-400,N));y=int(rng.integers(0,N))
    d.arc((x,y,x+int(rng.integers(200,700)),y+int(rng.integers(40,120))),0,180,fill=int(rng.integers(14,55)),width=int(rng.integers(1,9)))
wipes=np.asarray(im.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)/255
save(np.array([.13,.235,.16])[None,None,:]+wipes[...,None]*.12+fine[...,None]*.025,'board_wiped','color')
# 原创糖果罐印刷：所有字和圆章落在 2K 色彩图上，不用浮雕几何冒充油墨。
im=Image.new('RGB',(N,N),(135,27,19));d=ImageDraw.Draw(im)
d.rectangle((0,0,N,520),fill=(229,220,187))
d.text((190,145),'D R O P S',font=font(225),fill=(58,51,39))
d.text((390,420),'FRUIT CANDY',font=font(75),fill=(85,60,38))
d.ellipse((370,690,1678,1860),outline=(229,215,169),width=11)
d.ellipse((400,720,1648,1830),outline=(229,215,169),width=3)
d.text((650,950),'fruit',font=font(255),fill=(234,218,179))
d.text((590,1290),'フルーツドロップ',font=font(82),fill=(234,218,179))
d.text((735,1530),'SINCE 1958',font=font(55),fill=(234,218,179))
for x,y,r in [(870,1720,37),(960,1700,46),(1060,1720,39),(1160,1695,42)]:
    d.ellipse((x-r,y-r,x+r,y+r),outline=(234,218,179),width=5)
    d.arc((x,y-r-40,x+45,y-r+8),170,310,fill=(234,218,179),width=5)
path=OUT/'tin_label_color_2k.png';im.save(path)
record(path,'Original fictional candy packaging; vector/text rasterization; not source-film label','color')
(ROOT/'00_admin/texture_dependencies.json').write_text(json.dumps({'date':'2026-09-08','files':records},ensure_ascii=False,indent=2),encoding='utf-8')
print('TEXTURES_READY',len(records),flush=True)
