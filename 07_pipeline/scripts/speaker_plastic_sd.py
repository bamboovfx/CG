"""制作喇叭旧塑料 SD 原生图；输入为 Adobe 节点，输出为可编辑 SBS 与 4K PBR。

参考仅用于观察：Malte Resenberger-Loosmann 的 Plastic Worn；不嵌入参考图片。
保留原喇叭暖灰底色，分别控制注塑微纹、磨亮、粉化擦伤、细划痕。
"""
from pathlib import Path
import xml.etree.ElementTree as E
import subprocess, json, hashlib, uuid
import numpy as np
from PIL import Image
from build_desk_substance import Graph, put

R = Path(__file__).resolve().parents[2]
SD = Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M = R/'02_assets/materials/speaker_plastic'
T = R/'02_assets/textures/generated/speaker_plastic'
C = R/'07_pipeline/cache/speaker_plastic'
for folder in (M, T, C):
    folder.mkdir(parents=True, exist_ok=True)
g = Graph()
for element in (g.p, g.g):
    element.find('identifier').set('v', 'speaker_plastic')
g.p.find('fileUID').set('v', '{'+str(uuid.uuid5(uuid.NAMESPACE_URL, 'speaker-plastic-20260916'))+'}')
g.g.find('./attributes/label').set('v', 'Speaker worn plastic')
g.g.find('./attributes/description').set('v', 'Native layered plastic. Tile 25 cm. OpenGL normal. Warm grey original speaker color. Separate polish, scuff and scratches; optional asset wear mask, no metallic paint loss.')
tint = g.expose('PlasticColor', 'Plastic base color', (.71,.685,.605,1), '01 Plastic', typ='Float4')
rough = g.expose('BaseRoughness', 'Moulded plastic roughness', .46, '01 Plastic', .2,.8)
polish_amount = g.expose('PolishAmount', 'Contact polish', .85, '02 Wear')
scuff_amount = g.expose('ScuffAmount', 'Pale abrasion', .48, '02 Wear')
scratch_amount = g.expose('ScratchAmount', 'Hairline visibility', .58, '02 Wear')
age_amount = g.expose('AgeAmount', 'Uneven ageing', .34, '02 Wear')
depth = g.expose('ReliefDepth', 'Relief range in cm', .012, '03 Scale', .001,.02)
tile = g.expose('TileSize', 'Tile width in cm', 25, '03 Scale', 5,100)


def rotate(src, angle, x, y):
    """输入灰度层、旋转角与节点位置，返回旋转后的 SD 原生图输出。"""
    return g.inst('Crossing scratch direction', 'safe_transform', x,y, {'input':src},
                  {'rotation':('Float1',angle),'tile_safe_rotation':('Bool',0)}, graph='safe_transform_grayscale')


# 毫米以下注塑颗粒与厘米级旧化分开，避免全表面像石头一样起伏。
grain = g.inst('Fine moulded texture', 'noise_clouds_2',0,0, params={'scale':('Int1',11),'randomseed':('Int32',213)})
cloud = g.inst('Broad age variation', 'noise_clouds_2',0,360, params={'scale':('Int1',3),'randomseed':('Int32',312)})
zones = g.inst('Isolated handled areas', 'noise_bnw_spots_2',0,720, params={'scale':('Int1',2),'randomseed':('Int32',812)})
zones = g.inst('Soft polish boundaries', 'blur_hq',300,720, {'Source':zones}, {'Intensity':('Float1',5),'Quality':('Int1',1)}, graph='blur_hq_grayscale')
polish = g.levels('Preserve undisturbed areas',zones,600,720,.35,.65)
scuff_noise = g.inst('Abrasion breakup', 'noise_dirt_3',0,1100, params={'scale':('Int1',5),'randomseed':('Int32',174)})
scuff = g.blend('Abrasion is locally clustered',polish,scuff_noise,900,1080,mode=3)
scuff = g.levels('Broken pale scuff islands',scuff,1200,1080,.15,.65)
extra = g.image_input('ExtraWear',600,1430)
scuff = g.blend('Optional selected asset wear',scuff,extra,1500,1080,mode=5)

# 不同方向和长度的划痕分层，深度远小于模型倒角。
fine = g.inst('Fine handling hairlines','scratches_generator',0,1800,params={'scratches_amount':('Int1',650),'scratches_scale':('Float1',.045),'randomseed':('Int32',742)})
fine = rotate(fine,.12,300,1800)
long = g.inst('Sparse longer scratches','scratches_generator',0,2170,params={'scratches_amount':('Int1',28),'scratches_scale':('Float1',.24),'randomseed':('Int32',419)})
long = rotate(long,-.21,300,2170)
scratch = g.blend('Crossed lengths',fine,long,650,1950,mode=5)
scratch = g.levels('Bring faint generator hairlines into usable range',scratch,650,2650,.015,.19)
scratch = g.blend('Local handling distribution',scratch,g.levels('Sparse background scratches',polish,650,2350,outlow=.18,outhigh=1),1000,1950,mode=3)

# 同一种塑料：擦伤变浅、接触区变亮，金属度始终为零。
base = g.uniform('Original warm grey shell',(.71,.685,.605,1),1800,0,tint)
aged = g.uniform('Slight warm aged tint',(.59,.565,.485,1),1800,330)
base = g.blend('Slow subtle ageing',base,aged,2100,0,cloud,opacity=age_amount)
pale = g.uniform('Stress whitening / shallow abrasion',(.79,.765,.69,1),2100,330)
base = g.blend('Pale abrasion patches',base,pale,2400,0,scuff,opacity=scuff_amount)
base = g.blend('Fine light cuts',base,pale,2700,0,scratch,opacity=scratch_amount)
r = g.uniform('Base satin roughness',.46,1800,720,rough)
r = g.blend('Low amplitude moulded roughness',r,g.levels('Mould finish',grain,1450,430,outlow=.40,outhigh=.55),2100,720,opacity=.22)
r = g.blend('Handled zones become smoother',r,g.uniform('Polished plastic',.19,2100,1080),2400,720,polish,opacity=polish_amount)
r = g.blend('Scuffed plastic scatters light',r,g.uniform('Abrasion roughness',.62,2400,1080),2700,720,scuff,opacity=scuff_amount)
r = g.blend('Hairlines interrupt highlights',r,g.uniform('Scratch roughness',.66,2700,1080),3000,720,scratch,opacity=scratch_amount)
h = g.levels('Microscopic mould texture',grain,1800,1650,outlow=.46,outhigh=.54)
h = g.blend('Flatten touched mould grain',h,g.uniform('Smoothed surface',.50,1800,1970),2100,1650,polish,opacity=polish_amount)
h = g.blend('Shallow cuts into polymer',h,g.uniform('Cut depth',.18,2100,1970),2400,1650,scratch,opacity=scratch_amount)
normal = g.inst('Physical scale OpenGL normal','height_to_normal_world_units',2800,1650,{'input':h},{'surface_size':tile,'height_depth':depth,'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
outputs = [('BaseColor',base,'baseColor'),('Roughness',r,'roughness'),('Normal',normal,'normal'),('Height',h,'height'),('Metallic',g.uniform('Dielectric polymer',0,2900,2150),'metallic'),('PolishMask',polish,None),('ScuffMask',scuff,None),('ScratchMask',scratch,None)]
for i,(name,src,usage) in enumerate(outputs):
    g.output(name,src,3500,i*330,usage)
# 默认节点名称保持原样；用途只写入独立注释框。
for title,x,y in g.labels:
    q=put(g.gui,'GUIObject');put(q,'type','COMMENT');lay=put(q,'GUILayout')
    put(lay,'gpos',f'{x-65} {y-95} -100');put(lay,'size','245 55')
    put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title)
    put(q,'frameColor','0.18 0.24 0.28 0.8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
source=M/'speaker_plastic.sbs'
E.indent(g.p);E.ElementTree(g.p).write(source,encoding='utf-8',xml_declaration=True)
commands=[[str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')],
          [str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(T),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
for i,command in enumerate(commands):
    with (C/f'sd_{i}.log').open('w') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[]
for p in T.glob('*.png'):
    im=Image.open(p);a=np.asarray(im,dtype=float)
    files.append({'path':str(p.relative_to(R)),'size':im.size,'range':[float(a.min()),float(a.max())],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'color_space':'sRGB' if p.stem=='BaseColor' else 'Non-Color'})
report={'date':'2026-09-16','method':'Native Adobe Substance Designer graph and SAT renderer','source':str(source.relative_to(R)),'reference':'https://substance3d.adobe.com/community-assets/assets/eb6b672e0665fbdefa374e4ddd97e7c45037ff97','reference_author':'Malte Resenberger-Loosmann','reference_use':'Visual reference only; no third-party files incorporated','tile_metres':.25,'height_range_metres':.00012,'seed':3087,'normal':'OpenGL','nodes':len(g.nodes),'commands':commands,'files':files}
(T/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'nodes':len(g.nodes),'outputs':len(files),'source':str(source)}))
