"""制作独立表现层蒙版与原生SD归档；不重制已认可的imagegen木纹工艺层。

输入：Tripo木板投影凸包、既有长划痕；输出：可控老化／磨损及损伤高度。
高度由Blender按米制距离解释，掠射光可检验；所有蒙版为数学生成。
"""
from pathlib import Path
import json
import hashlib
import subprocess
import uuid
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageFilter
from build_desk_substance import Graph
from wood_layers_sd import annotate
from tripo_wood_reference_sd import resource

ROOT=Path(__file__).resolve().parents[2]
TEX=ROOT/'02_assets/textures/generated/tripo_wood_appearance'
OLD=ROOT/'02_assets/textures/generated/tripo_wood_reference'
MAT=ROOT/'02_assets/materials/tripo_wood_appearance'
WORK=ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930'
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
SIZE=2048
PARAMS={'Scratches':.95,'Age':.72,'Wear':.88}


def field(rng, x, y=None):
    """输入随机源与格点宽高，返回归一化连续场；不采样实物照片。"""
    a=(rng.random((y or x,x))*65535).astype(np.uint16)
    return np.asarray(Image.fromarray(a).convert('F').resize((SIZE,SIZE),Image.Resampling.BICUBIC),dtype=np.float32)/65535


def save(array, path):
    """输入0–1标量结构和目标路径，保存16位无色彩转换PNG。"""
    Image.fromarray((np.clip(array,0,1)*65535).astype(np.uint16)).save(path)


def generate(board, hull):
    """输入板类型与UV凸包，返回贴合真实圆角和使用接触区的独立损伤图。"""
    out=TEX/board/'structure'; out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(93041+(board=='back'))
    u=np.linspace(0,1,SIZE,dtype=np.float32)[None,:]
    v=np.linspace(1,0,SIZE,dtype=np.float32)[:,None]
    # 凸包有向距离让磨损贴合真实板轮廓，圆角也能落到蒙版内。
    edge=np.ones((SIZE,SIZE),np.float32)
    for a,b in zip(hull,hull[1:]+hull[:1]):
        dx=b[0]-a[0]; dy=b[1]-a[1]
        distance=(dx*(v-a[1])-dy*(u-a[0]))/max((dx*dx+dy*dy)**.5,1e-8)
        np.minimum(edge,distance,out=edge)
    coarse=field(rng,9); medium=field(rng,65); micro=field(rng,500)
    fibres=field(rng,17,650)
    age_seed=np.zeros_like(edge); dark_seed=np.zeros_like(edge); contact=np.zeros_like(edge)
    # 老化分两种：涂层发暗和局部褪色；接触磨损另有自己的分布。
    patches=[(.28,.69,.21,.16,.80),(.73,.35,.15,.22,.58),(.59,.88,.17,.10,.62)] if board=='seat' else [(.22,.53,.19,.24,.64),(.75,.76,.18,.18,.63)]
    for x,y,sx,sy,strength in patches:
        age_seed+=strength*np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.5)
    for x,y,sx,sy in [(.12,.28,.21,.14),(.80,.69,.19,.15),(.48,.11,.28,.12)]:
        dark_seed+=np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.7)
    contacts=[(.22,.93,.16,.07),(.77,.94,.15,.06),(.20,.68,.10,.07),(.69,.40,.08,.065),(.51,.88,.11,.055)] if board=='seat' else [(.05,.52,.055,.20),(.87,.91,.11,.055),(.68,.12,.12,.04)]
    for x,y,sx,sy in contacts:
        contact+=np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.7)
    # 稀疏破碎的涂层岛，不让老化只成为一层均匀棕色滤镜。
    bleach=np.clip(age_seed*(.45+.8*coarse),0,1)
    dark=np.clip(dark_seed*(.25+.50*coarse)+np.clip(1-edge/.07,0,1)*.18,0,1)
    # 木纤维参与破损边界，避免二维圆斑看起来像迷彩或白漆。
    chips=np.clip((medium*.54+fibres*.36+micro*.10-.48)/.16,0,1)
    ageing_loss=np.clip((age_seed-.28)/.40,0,1)*chips
    # 前缘为UV v=1；座面靠前接触区最明显，圆角间断露木。
    edge_width=.012+.023*np.clip((coarse-.40)/.35,0,1)
    edge_band=np.clip(1-edge/edge_width,0,1)
    breakup=np.clip((medium*.55+fibres*.35+micro*.10-.39)/.26,0,1)
    wear=np.maximum(edge_band*breakup,np.clip(contact*1.4,0,1)*chips*.85)
    wear*=np.clip(edge/.0018,0,1)
    relief=np.clip(wear*(.72+.28*fibres),0,1)
    age_relief=ageing_loss*(.74+.26*micro)
    # 延用用户已认可的长划痕位置；稍加宽，使正常机位也能读出沟槽。
    scratch={}
    for name in ('ScratchDark','ScratchLight'):
        im=Image.open(OLD/board/(name+'.png')).convert('I').resize((SIZE,SIZE))
        arr=np.asarray(im,dtype=np.float32)/65535
        # 短划痕保持低对比，避免每条都变成同深的刻痕。
        scratch[name]=arr*(.38 if name=='ScratchDark' else .70)
    lines=[(.14,.46,.31,.18,.0009),(.21,.44,.37,.25,.00065),(.64,.53,.79,.28,.0008),
           (.69,.60,.84,.37,.00055),(.40,.69,.55,.53,.00065),(.52,.64,.60,.42,.0005),
           (.08,.27,.21,.17,.0007),(.59,.25,.77,.22,.00055),(.38,.37,.51,.48,.00045),(.79,.65,.90,.52,.00065)]
    if board=='back': lines=[(.24,.65,.45,.64,.00055),(.69,.31,.81,.41,.0005)]
    for index,(x0,y0,x1,y1,width) in enumerate(lines):
        dx=x1-x0; dy=y1-y0; t=np.clip(((u-x0)*dx+(v-y0)*dy)/(dx*dx+dy*dy),0,1)
        distance=np.sqrt((u-x0-dx*t)**2+(v-y0-dy*t-.0014*np.sin(t*8+index))**2)
        groove=np.exp(-(distance/(width*1.35*(.75+.35*micro)))**2)*(.63+.37*micro)
        target='ScratchLight' if index%3==0 else 'ScratchDark'
        np.maximum(scratch[target],groove,out=scratch[target])
    maps={'AgeBleach':bleach,'AgeDark':dark,'AgeLoss':ageing_loss,'AgeRelief':age_relief,
          'WearMask':wear,'WearRelief':relief,**scratch}
    stats={}
    for name,array in maps.items():
        save(array,out/(name+'.png'))
        stats[name]={'mean':float(array.mean()),'coverage_above_0.25':float((array>.25).mean()),'max':float(array.max())}
    return out,stats


def build(board,hull):
    """输入木板和轮廓，编译可调SD表现层；所有Raw图都保留便于重新设计。"""
    folder,stats=generate(board,hull)
    out=TEX/board; g=Graph(); identifier='wood_appearance_'+board
    for item in (g.p,g.g): item.find('identifier').set('v',identifier)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,identifier+'20260930'))+'}')
    g.g.find('./attributes/label').set('v','Wood appearance / '+board)
    g.g.find('./attributes/description').set('v','Only appearance masks and coating damage. Approved imagegen veneer process remains in its original package. Age: fading, darkening and finish loss; Wear: contact and true silhouette edges. Relief is normalized depression; Blender distance 0.12/0.22 mm, no silhouette displacement.')
    controls={k:g.expose(k,k,v,'表现层独立强度') for k,v in PARAMS.items()}
    zero=g.uniform('零表现',0,0,0)
    outputs=[]
    for name in stats:
        raw=resource(g,folder/(name+'.png'),'结构／'+name)
        effect='Scratches' if name.startswith('Scratch') else 'Age' if name.startswith('Age') else 'Wear'
        signal=g.blend('表现／'+name,zero,raw,0,0,opacity=controls[effect])
        g.output(name,signal,0,0); g.output('Raw_'+name,raw,0,0)
        outputs += [name,'Raw_'+name]
    annotate(g); path=MAT/(identifier+'.sbs'); E.indent(g.p)
    E.ElementTree(g.p).write(path,encoding='utf-8',xml_declaration=True)
    commands=[[str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')],
              [str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(out),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
    for k,command in enumerate(commands):
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/f'{board}_appearance_sd_{k}.txt').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-3000:])
    return {'board':board,'source':str(path.relative_to(ROOT)),'outputs':outputs,'structure_stats':stats}


def main():
    """保护旧工艺贴图，制作两块板的表现配方和来源清单。"""
    for folder in (TEX,MAT,WORK): folder.mkdir(parents=True,exist_ok=True)
    inspection=json.loads((WORK/'input_inspection.json').read_text(encoding='utf-8'))
    protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OLD.glob('*/Process_*.png')}
    boards=[build(board,inspection['boards'][obj]['uv_hull']) for board,obj in [('seat','LP_part_02'),('back','LP_part_09')]]
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    manifest={'boards':boards,'parameters':PARAMS,'mask_authoring_resolution':SIZE,'output_resolution':4096,
              'protected_process_files':protected,'approved_process_unchanged':True,
              'height_distance_m':{'age':.00012,'wear':.00022,'scratch':.00010}}
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'boards':len(boards),'approved_process_unchanged':True}),flush=True)


if __name__=='__main__': main()
