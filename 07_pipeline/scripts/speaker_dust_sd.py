"""SD 原生节点生成粉尘覆盖和细颗粒；模型朝向/缝隙在着色时决定积尘位置。"""
from pathlib import Path
import xml.etree.ElementTree as E
import subprocess,json,uuid,hashlib
from PIL import Image
from build_desk_substance import Graph,put

R=Path(__file__).resolve().parents[2];SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/speaker_dust';T=R/'02_assets/textures/generated/speaker_dust';C=R/'07_pipeline/cache/speaker_dust'
for p in (M,T,C):p.mkdir(parents=True,exist_ok=True)
g=Graph()
for e in (g.p,g.g):e.find('identifier').set('v','speaker_dust')
g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'speaker_dust_20260916'))+'}')
g.g.find('./attributes/label').set('v','Settled powder dust')
g.g.find('./attributes/description').set('v','Native dust coverage and grain. 20 cm tile. Combine with upward normals and cavity placement in asset shader. No baked lighting.')
coverage=g.expose('Coverage','Dust continuity',.90,'Dust',0,1)
macro=g.inst('Dust clusters','noise_bnw_spots_2',0,0,params={'scale':('Int1',2),'randomseed':('Int32',913)})
micro=g.inst('Fine powder granules','noise_dirt_3',0,400,params={'scale':('Int1',13),'randomseed':('Int32',531)})
soft=g.inst('Soft settled islands','blur_hq',300,0,{'Source':macro},{'Intensity':('Float1',2),'Quality':('Int1',1)},graph='blur_hq_grayscale')
field=g.blend('Broad coverage broken by grains',soft,micro,620,0,opacity=.10)
mask=g.levels('Visible but discontinuous dust',field,950,0,.22,.68,.05,1)
mask=g.blend('Public dust coverage',g.uniform('Clear',0,650,400),mask,1250,0,opacity=coverage)
grain=g.levels('Powder relief',micro,950,500,outlow=.2,outhigh=.8)
g.output('DustMask',mask,1550,0)
g.output('Grain',grain,1550,500)
for title,x,y in g.labels:
    q=put(g.gui,'GUIObject');put(q,'type','COMMENT');ly=put(q,'GUILayout');put(ly,'gpos',f'{x-50} {y-90} -100');put(ly,'size','240 55');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
src=M/'speaker_dust.sbs';E.indent(g.p);E.ElementTree(g.p).write(src,encoding='utf-8',xml_declaration=True)
commands=[[str(SD/'sbscooker.exe'),'--inputs',str(src),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')],[str(SD/'sbsrender.exe'),'render','--inputs',str(src.with_suffix('.sbsar')),'--output-path',str(T),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report']]
for i,cmd in enumerate(commands):
    with (C/f'dust_sd_{i}.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
(T/'manifest.json').write_text(json.dumps({'date':'2026-09-16','method':'Native Adobe Substance Designer procedural nodes','seed':3087,'tile_metres':.2,'source':str(src.relative_to(R)),'commands':commands,'files':[{'path':str(p.relative_to(R)),'size':Image.open(p).size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'colorspace':'Non-Color'} for p in T.glob('*.png')]},indent=2),encoding='utf-8')
print('SD dust masks rendered')
