"""原生SD制作浅黄胶脚：模塑工艺与轻度老化／擦伤／脏渍，内容与物体位置分开。"""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import xml.etree.ElementTree as E
from PIL import Image
from build_desk_substance import Graph
from wood_layers_sd import annotate

ROOT = Path(__file__).resolve().parents[2]
SD = Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
MAT = ROOT/'02_assets/materials/chair_foot_caps'
TEX = ROOT/'02_assets/textures/generated/chair_foot_caps'
WORK = ROOT/'07_pipeline/cache/chair_foot_cap_materials_20261001'


def build():
    """输入Adobe原生节点库，输出18张4K通道、SBS源／SBSAR与尺寸哈希清单。"""
    for folder in [MAT,TEX,WORK]:
        folder.mkdir(parents=True,exist_ok=True)
    g=Graph()
    identifier='chair_foot_caps'
    for element in [g.p,g.g]:
        element.find('identifier').set('v',identifier)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,identifier+'20261001'))+'}')
    g.g.find('./attributes/label').set('v','Foot caps: process and appearance')
    g.g.find('./attributes/description').set('v','Pale yellow matte polymer. Metallic=0. Original procedural 4K content at 0.08m tile. Age, wear, scratches and dirt separate; object-level top/bottom/contact placement in Blender. No rust, exposed steel or baked lighting. OpenGL normal for conventional UV; Blender uses explicit triplanar height.')
    tint=g.expose('BaseColor','Pale yellow polymer',(.75,.73,.62,1),'01 Process',typ='Float4')
    roughness=g.expose('BaseRoughness','Matte moulded finish',.61,'01 Process',.3,.9)
    controls={k:g.expose(k,k,1,'02 Appearance') for k in ['Age','Wear','Scratches','Dirt']}
    zero=g.uniform('Metallic=0／蒙版零值',0,0,0)
    one=g.uniform('独立AO=1／平面通道',1,0,0)
    cloud=g.inst('缓慢模塑色差','noise_clouds_2',0,0,params={'scale':('Int1',2),'randomseed':('Int32',631)})
    fine=g.inst('模塑微细颗粒','noise_dirt_3',0,0,params={'scale':('Int1',8),'randomseed':('Int32',743)})
    spots=g.inst('稀疏擦伤分布','noise_bnw_spots_2',0,0,params={'scale':('Int1',6),'randomseed':('Int32',371)})
    grime=g.inst('附着物颗粒','noise_dirt_3',0,0,params={'scale':('Int1',7),'randomseed':('Int32',981)})
    base=g.uniform('工艺／浅黄胶质',(.75,.73,.62,1),0,0,exposed=tint)
    base=g.blend('工艺／微弱色差',base,g.uniform('模塑微暗色',(.735,.715,.603,1),0,0),0,0,cloud,opacity=.12)
    rough=g.blend('工艺／粗糙度控制',zero,one,0,0,opacity=roughness)
    rough=g.blend('工艺／细微反射变化',rough,g.levels('颗粒粗糙度',fine,0,0,outlow=.53,outhigh=.72),0,0,opacity=.18)
    height=g.levels('工艺／微起伏20微米标尺',fine,0,0,outlow=.46,outhigh=.54)
    normal=g.filt('工艺／OpenGL法线','normal',0,0,{'input1':height},{'intensity':('Float1',.10),'inversedy':('Bool',0)},channels=1)
    # 独立宏观老化场保留完好区；降低擦伤阈值，确保3cm胶脚能采到有效区域。
    ageing=g.inst('局部黄化分布','noise_bnw_spots_2',0,0,params={'scale':('Int1',3),'randomseed':('Int32',177)})
    age=g.levels('局部黄化／灰化分布',ageing,0,0,.30,.70)
    wear=g.levels('浅擦伤／褪光斑',spots,0,0,.35,.65)
    wear=g.filt('擦伤边缘破碎','warp',0,0,{'input1':wear,'inputgradient':fine},{'intensity':('Float1',.00035)})
    scratch=g.inst('稀疏细划痕','pattern_scratches_generator',0,0,params={
        'spline_number':('Int1',56),'spline_scale':('Float1',.18),'spline_width':('Float1',10.0),
        'spline_width_in_pixel':('Bool',1),'spline_rotation_random':('Float1',.85),
        'spline_scale_random':('Float1',.65),'spline_distortion_random':('Float1',.08),
        'randomseed':('Int32',318)},graph='scratches_generator')
    dirt=g.levels('灰尘／泥渍不均匀边缘',grime,0,0,.15,.40)
    dirt_color=g.blend('脏渍／灰褐多色',g.uniform('积灰色',(.26,.255,.225,1),0,0),
                       g.uniform('浅泥色',(.41,.35,.26,1),0,0),0,0,cloud)
    dirt_color=g.blend('脏渍／细暗点',dirt_color,g.uniform('暗颗粒',(.15,.15,.13,1),0,0),0,0,
                       g.levels('稀疏暗颗粒',fine,0,0,.73,.86),opacity=.5)
    dirt_h=g.levels('脏渍／轻微附着厚度',grime,0,0,outlow=.1,outhigh=.75)
    masks={k:g.blend(k+'独立控制',zero,v,0,0,opacity=controls[p]) for k,v,p in [
        ('AgeMask',age,'Age'),('WearMask',wear,'Wear'),('ScratchMask',scratch,'Scratches'),('DirtMask',dirt,'Dirt')]}
    outputs={'Process_BaseColor':(base,None),'Process_Roughness':(rough,None),
             'Process_Metallic':(zero,None),'Process_Height':(height,None),'Process_Normal':(normal,None),'Process_AO':(one,None)}
    outputs.update({k:(v,None) for k,v in masks.items()})
    outputs.update({'DirtColor':(dirt_color,None),'DirtHeight':(dirt_h,None)})
    # 通用SD样片与Blender资产定位分开，旧化强度归零时六个最终通道恢复工艺。
    fc=g.blend('SD样片／黄化',base,g.uniform('温和老化色',(.69,.60,.37,1),0,0),0,0,masks['AgeMask'],opacity=.75)
    fc=g.blend('SD样片／擦伤泛白',fc,g.uniform('磨损泛白色',(.84,.82,.72,1),0,0),0,0,masks['WearMask'],opacity=.80)
    fc=g.blend('SD样片／划痕色',fc,g.uniform('划痕微暗色',(.46,.43,.33,1),0,0),0,0,masks['ScratchMask'],opacity=.70)
    fc=g.blend('SD样片／浅脏渍',fc,dirt_color,0,0,masks['DirtMask'],opacity=.55)
    fr=g.blend('SD样片／老化褪光',rough,g.uniform('老化粗糙度',.70,0,0),0,0,masks['AgeMask'])
    fr=g.blend('SD样片／磨损粗糙度',fr,g.uniform('擦伤粗糙度',.76,0,0),0,0,masks['WearMask'])
    fr=g.blend('SD样片／脏渍粗糙度',fr,g.uniform('脏渍粗糙度',.82,0,0),0,0,masks['DirtMask'],opacity=.3)
    fh=g.blend('SD样片／划痕浅凹',height,g.uniform('划痕高度',.40,0,0),0,0,masks['ScratchMask'],opacity=.5)
    fh=g.blend('SD样片／附着微起伏',fh,dirt_h,0,0,masks['DirtMask'],opacity=.1)
    fn=g.filt('SD样片／最终OpenGL法线','normal',0,0,{'input1':fh},{'intensity':('Float1',.10),'inversedy':('Bool',0)},channels=1)
    for name,signal,usage in [('Final_BaseColor',fc,'baseColor'),('Final_Roughness',fr,'roughness'),
                             ('Final_Metallic',zero,'metallic'),('Final_Height',fh,'height'),
                             ('Final_Normal',fn,'normal'),('Final_AO',one,'ambientOcclusion')]:
        outputs[name]=(signal,usage)
    for name,(signal,usage) in outputs.items():
        g.output(name,signal,0,0,usage)
    annotate(g)
    path=MAT/(identifier+'.sbs')
    E.indent(g.p)
    E.ElementTree(g.p).write(path,encoding='utf-8',xml_declaration=True)
    commands=[
        [str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')],
        [str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(TEX),
         '--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
    for index,command in enumerate(commands):
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/f'sd_{index}.log').write_text(done.stdout+done.stderr,encoding='utf-8')
        assert done.returncode==0,(done.stdout+done.stderr)[-2500:]
    files=[]
    for file in TEX.glob('*.png'):
        with Image.open(file) as im:
            assert im.size==(4096,4096)
            files.append({'name':file.name,'pixels':list(im.size),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    manifest={'source':str(path.relative_to(ROOT)),'tile_m':.08,'resolution':4096,
              'normal':'OpenGL','controls':list(controls),'nodes':len(g.nodes),'outputs':files,
              'source_kind':'Original native procedural Substance graph; photograph used only for visual reference'}
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FOOT_CAPS_SD '+json.dumps({'nodes':len(g.nodes),'outputs':len(files)}),flush=True)


if __name__=='__main__':
    build()
