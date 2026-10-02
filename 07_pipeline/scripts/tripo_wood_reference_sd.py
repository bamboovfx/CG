"""按课椅参考制作宽幅生长纹与使用痕迹，再构建原生SD五通道材质。

输入：人工观察参考的纹理方向、弧线、划痕位置；不采样参考照片像素。
输出：座面／靠背独立SBS、SBSAR、4K工艺通道和独立表现蒙版。
参数：归一化木板坐标；所有结构蒙版由数学函数和可复现随机种子生成。
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import uuid
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageDraw
from build_desk_substance import Graph, put
from wood_layers_sd import annotate

ROOT=Path(__file__).resolve().parents[2]
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
MAT=ROOT/'02_assets/materials/tripo_wood_reference'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_reference'
WORK=ROOT/'07_pipeline/cache/tripo_wood_reference_20260930'
SIZE=4096


def save_mask(array, path):
    """输入0–1结构信号和路径，输出16位灰度PNG；不处理任何参考照片。"""
    Image.fromarray(np.clip(array*65535,0,65535).astype(np.uint16)).save(path)


def noise(rng, side):
    """输入随机源和格点数量，返回4K平滑随机场，用于木纤维不规则变化。"""
    a=(rng.random((side,side))*65535).astype(np.uint16)
    return np.asarray(Image.fromarray(a).convert('F').resize((SIZE,SIZE),Image.Resampling.BICUBIC),dtype=np.float32)/65535


def structure(board):
    """输入座板／背板标识，生成宽幅弧形木纹、长短划痕、老化与边缘缺口。"""
    folder=TEX/board/'structure'; folder.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(20260930+(board=='back'))
    # 图像上缘对应木板后侧／背板上缘，Blender UV保持同一方向。
    u=np.linspace(0,1,SIZE,dtype=np.float32)[None,:]
    v=np.linspace(1,0,SIZE,dtype=np.float32)[:,None]
    n=noise(rng,32); low=noise(rng,6)
    if board=='seat':
        # 椭圆年轮中心放在板外，形成参考中横贯座面的宽幅扫弧。
        r=np.sqrt(((u-.20)*.84)**2+((v-1.46)*.92)**2)
        phase=r*19.5+.13*np.sin(u*6.0+v*2.0)+.08*(low-.5)
    else:
        phase=v*15.0+.80*(u-.52)**2+.15*np.sin(u*5.0)+.10*(low-.5)
    fraction=np.mod(phase,1)
    growth=np.exp(-((fraction-.76)/.095)**2)
    broad=.52+.22*np.cos(phase*2*np.pi)-.26*growth
    # 细纤维沿宽幅生长纹变化，低对比保留；不让粗噪声冒充木纹。
    fibre=np.sin((phase*21+.75*n+.22*np.sin(u*33))*2*np.pi)
    grain=np.clip(broad+.052*fibre+.065*(n-.5),0,1)
    save_mask(grain,folder/'Growth.png')
    save_mask(.5+.18*fibre,folder/'Fibre.png')
    save_mask(low,folder/'Age.png')
    # 手工定向的长使用划痕：参考可见斜向交叉沟槽，长度与板尺寸对应。
    lines=[(.14,.46,.31,.18,.0009),(.21,.44,.37,.25,.00065),
        (.64,.53,.79,.28,.0008),(.69,.60,.84,.37,.00055),
        (.40,.69,.55,.53,.00065),(.52,.64,.60,.42,.0005),
        (.08,.27,.21,.17,.0007),(.59,.25,.77,.22,.00055),
        (.38,.37,.51,.48,.00045),(.79,.65,.90,.52,.00065)]
    if board=='back': lines=[(.24,.65,.45,.64,.00055),(.69,.31,.81,.41,.0005)]
    dark=np.zeros((SIZE,SIZE),np.float32); light=dark.copy()
    for index,(x0,y0,x1,y1,width) in enumerate(lines):
        dx=x1-x0; dy=y1-y0; t=np.clip(((u-x0)*dx+(v-y0)*dy)/(dx*dx+dy*dy),0,1)
        # 微弯曲、不齐宽和断续让划痕脱离规则直线。
        px=x0+dx*t; py=y0+dy*t+.0014*np.sin(t*8+index)
        dist=np.sqrt((u-px)**2+(v-py)**2)
        mark=np.exp(-(dist/(width*(.65+.50*n)))**2)*(0.46+.54*n)
        target=dark if index%3 else light
        np.maximum(target,mark,out=target)
    # 几十条轻微短划痕和少量黑色凹点，按座面使用区域分布。
    canvas=Image.new('L',(SIZE,SIZE)); draw=ImageDraw.Draw(canvas)
    for _ in range(75 if board=='seat' else 28):
        x=float(rng.uniform(.07,.93)); y=float(rng.uniform(.07,.90))
        length=float(rng.uniform(.007,.050)); angle=float(rng.uniform(-1.5,1.5))
        draw.line([(x*SIZE,(1-y)*SIZE),((x+length*np.cos(angle))*SIZE,(1-y-length*np.sin(angle))*SIZE)],fill=int(rng.uniform(90,195)),width=int(rng.integers(1,3)))
    for _ in range(24 if board=='seat' else 10):
        x=float(rng.uniform(.06,.94)*SIZE); y=float(rng.uniform(.08,.93)*SIZE)
        radius=float(rng.uniform(1,4)); draw.ellipse((x-radius,y-radius,x+radius,y+radius*1.8),fill=int(rng.uniform(110,225)))
    fine=np.asarray(canvas,dtype=np.float32)/255
    save_mask(np.maximum(dark,fine),folder/'ScratchDark.png')
    save_mask(light,folder/'ScratchLight.png')
    edge=np.minimum(np.minimum(u,1-u),np.minimum(v,1-v))
    # 参考是窄边间断露木，不能生成连续18mm浅色装饰带。
    breakup=np.clip((noise(rng,110)-.52)/.27,0,1)
    wear=np.clip(1-edge/.012,0,1)*breakup
    save_mask(wear,folder/'Wear.png')
    # 靠背背面残损的矩形印记：匹配位置和轮廓，不猜测难以辨认的品牌文字。
    stamp=np.zeros_like(grain)
    if board=='back':
        rect=(u>.48)&(u<.77)&(v>.25)&(v<.41)
        mesh=(np.sin(u*285)+np.sin(v*245)>.12)
        stamp=rect*mesh*np.clip((noise(rng,160)-.30)/.45,0,1)
    save_mask(stamp,folder/'Stamp.png')
    return folder


def resource(g, path, label, color_mode=False):
    """输入Graph、位图和颜色模式，创建包内资源并返回4K输出句柄。"""
    did=g.uid(); d=put(g.deps,'dependency'); put(d,'filename','?himself'); put(d,'uid',did)
    put(d,'type','package'); put(d,'fileUID',0); put(d,'versionUID',0)
    r=put(g.p.find('content'),'resource'); name=path.stem
    for key,value in [('identifier',name),('uid',g.uid()),('type','bitmap'),('format','png'),('colorSpace','[use_embedded_profile]' if color_mode else '[linear]'),('filepath',path.as_posix())]: put(r,key,value)
    h=g.filt(label,'bitmap',0,0,params={'bitmapresourcepath':('String',f'pkg:///{name}?dependency={did}'),'colorswitch':('Bool',int(color_mode))},channels=1 if color_mode else 2)
    p=g.nodes[-1].find('./compImplementation/compFilter/parameters/parameter'); p.find('relativeTo').set('v','0'); p.find('./paramValue/constantValueInt2').set('v','12 12')
    return h


def build(board):
    """输入木板标识，输出原生SD分层配方、归档与4K通道；保留独立蒙版。"""
    folder=structure(board); out=TEX/board; g=Graph(); identifier='reference_wood_'+board
    for item in (g.p,g.g): item.find('identifier').set('v',identifier)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,identifier+'20260930'))+'}')
    g.g.find('./attributes/label').set('v','Reference school wood / '+board)
    g.g.find('./attributes/description').set('v','Artist-directed growth rings and use marks, observed from reference; no photo pixels sampled. Board-space mapping. Metallic zero. Masks authored procedurally; editable process/effect parameters.')
    sc=g.expose('Scratches','划痕强度',.90,'02 表现层')
    age=g.expose('Age','老化强度',.22,'02 表现层')
    wear=g.expose('Wear','边缘磨损强度',.75,'02 表现层')
    contrast=g.expose('GrainContrast','宽幅生长纹对比',1.0,'01 工艺层')
    finish=g.expose('FinishRoughness','旧涂层基础粗糙度',.39,'01 工艺层',.15,.75)
    coverage=g.expose('SurfaceSize','木板宽度（cm）',37.1 if board=='seat' else 36.1,'03 尺度',10,100)
    relief=g.expose('HeightRange','微起伏全高度范围（cm）',.018,'03 尺度',.005,.12)
    growth=resource(g,folder/'Growth.png','工艺层／人工定向宽幅生长纹')
    fibre=resource(g,folder/'Fibre.png','工艺层／顺纹细纤维')
    a=resource(g,folder/'Age.png','表现层／不均匀老化')
    dark=resource(g,folder/'ScratchDark.png','表现层／深划痕与凹点')
    light=resource(g,folder/'ScratchLight.png','表现层／浅色刮伤')
    w=resource(g,folder/'Wear.png','表现层／窄边间断露木')
    stamp=resource(g,folder/'Stamp.png','表现层／背面残损印记')
    c0=g.uniform('木纹暗部',(.44,.235,.065,1),0,0)
    c1=g.uniform('木纹浅部',(.72,.48,.17,1),0,0)
    figure=g.blend('工艺层／生长纹色差',c0,c1,0,0,growth)
    flat=g.uniform('蜜色旧涂层',(.59,.355,.11,1),0,0)
    # 改用内置imagegen生成的自然弧形木纹；条纹试验只保留为结构研究输出。
    source=resource(g,TEX/'reference_veneer_base.png','工艺层／参考导向自然宽幅木纹',True)
    if board=='back':
        source=g.filt('工艺层／背板裁取木纹上半部','transformation',0,0,{'input1':source},{'matrix22':('Float4',(1,0,0,.5)),'offset':('Float2',(0,.25))},channels=1)
        source=g.filt('工艺层／背板宽纹方向校正','transformation',0,0,{'input1':source},{'matrix22':('Float4',(0,1,-1,0))},channels=1)
    base=g.blend('工艺层／材质反射率校正',source,g.uniform('蜜色涂层滤色',(.60,.58,.61,1),0,0),0,0,mode=3)
    base=g.blend('工艺层／自然木纹对比控制',flat,base,0,0,opacity=contrast)
    fibre=g.filt('工艺层／自然木纤维结构','grayscaleconversion',0,0,{'input1':source},channels=2)
    # 高频木孔结构去掉宽幅色差，避免将年轮颜色当成整块凹凸。
    pores=g.inst('工艺层／分离顺纹孔隙','highpass',0,0,{'Source':fibre},{'Radius':('Float1',6)},graph='highpass_grayscale')
    pores=g.levels('工艺层／木孔微结构对比',pores,0,0,.465,.535,0,1)
    height=g.levels('工艺层／涂层下孔隙起伏',pores,0,0,outlow=.44,outhigh=.56)
    rough=g.blend('工艺层／基础粗糙度',g.uniform('粗糙度0',0,0,0),g.uniform('粗糙度1',1,0,0),0,0,opacity=finish)
    rough=g.blend('工艺层／顺纹孔隙反射',rough,g.levels('木孔反射范围',pores,0,0,outlow=.48,outhigh=.32),0,0,opacity=.45)
    rough=g.blend('工艺层／涂层局部反射',rough,g.levels('涂层反射范围',a,0,0,outlow=.32,outhigh=.51),0,0,opacity=.12)
    metallic=g.uniform('木材和清漆Metallic=0',0,0,0); ao=g.uniform('浅表细节AO独立白色',1,0,0)
    c=g.blend('老化／暖色涂层变暗',base,g.uniform('老化木色',(.39,.24,.09,1),0,0),0,0,a,opacity=age)
    c=g.blend('磨损／窄边露木',c,g.uniform('露木颜色',(.64,.49,.28,1),0,0),0,0,w,opacity=wear)
    c=g.blend('划痕／暗沟槽',c,g.uniform('划痕深色',(.17,.075,.021,1),0,0),0,0,dark,opacity=sc)
    c=g.blend('划痕／浅露木',c,g.uniform('浅色刮痕',(.76,.62,.36,1),0,0),0,0,light,opacity=sc)
    r=g.blend('老化／粗糙度',rough,g.uniform('老化粗糙度',.47,0,0),0,0,a,opacity=age)
    r=g.blend('磨损／粗糙度',r,g.uniform('露木粗糙度',.64,0,0),0,0,w,opacity=wear)
    scratch=g.blend('共享划痕分布',dark,light,0,0,mode=5)
    r=g.blend('划痕／粗糙度',r,g.uniform('划痕粗糙度',.62,0,0),0,0,scratch,opacity=sc)
    h=g.blend('划痕／浅凹槽',height,g.uniform('划痕高度',.35,0,0),0,0,scratch,opacity=sc)
    h=g.blend('磨损／露纤维',h,g.levels('露纤维高度',fibre,0,0,outlow=.49,outhigh=.51),0,0,w,opacity=wear)
    normals=[g.inst(label,'height_to_normal_world_units',0,0,{'input':hsrc},{'surface_size':coverage,'height_depth':relief,'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2') for label,hsrc in [('工艺层／OpenGL法线',height),('表现层／OpenGL法线',h)]]
    outputs=[('Process_BaseColor',base,None),('Process_Roughness',rough,None),('Process_Metallic',metallic,None),('Process_Normal',normals[0],None),('Process_AO',ao,None),('BaseColor',c,'baseColor'),('Roughness',r,'roughness'),('Metallic',metallic,'metallic'),('Normal',normals[1],'normal'),('AO',ao,'ambientOcclusion'),('Process_Height',height,None),('Height',h,None),('Growth',fibre,None),('Pores',pores,None),('ScratchDark',dark,None),('ScratchLight',light,None),('ScratchMask',scratch,None),('AgeMask',a,None),('WearMask',w,None),('StampMask',stamp,None)]
    for name,handle,usage in outputs: g.output(name,handle,0,0,usage)
    annotate(g); path=MAT/(identifier+'.sbs'); E.indent(g.p); E.ElementTree(g.p).write(path,encoding='utf-8',xml_declaration=True)
    commands=[[str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')],[str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(out),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
    for k,command in enumerate(commands):
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/f'{board}_sd_{k}.txt').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-4000:])
    return {'board':board,'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'commands':commands,'outputs':[name for name,_,_ in outputs],'parameters':{'Scratches':.9,'Age':.22,'Wear':.75,'GrainContrast':1.0,'FinishRoughness':.39,'HeightRange_cm':.018}}


def main():
    """生成两套独立木板材质并保存来源、参数与输出哈希清单。"""
    for folder in (MAT,TEX,WORK): folder.mkdir(parents=True,exist_ok=True)
    if '--back-only' in sys.argv:
        # 定向返工只重建背板，保留座板已通过的原生配方与输出。
        existing=json.loads((TEX/'manifest.json').read_text(encoding='utf-8'))
        results=[next(b for b in existing['boards'] if b['board']=='seat'),build('back')]
    else: results=[build(board) for board in ('seat','back')]
    manifest={'boards':results,'resolution':[SIZE,SIZE],'source_type':'built-in imagegen reference-directed veneer colour; mathematical height and artist-directed use marks','imagegen_source':str((TEX/'reference_veneer_base.png').relative_to(ROOT)),'imagegen_sha256':hashlib.sha256((TEX/'reference_veneer_base.png').read_bytes()).hexdigest(),'maps':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in TEX.glob('*/*.png')]}
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'boards':len(results),'maps':len(manifest['maps'])}))


if __name__=='__main__': main()
