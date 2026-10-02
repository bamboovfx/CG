"""Build native editable SD layers for dirty CRT glass and crossed handling scratches.

Inputs: installed Adobe procedural nodes; supplied images are visual references only.
Outputs: SBS/SBSAR and 4K 16-bit numeric masks, roughness and microscopic height.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import subprocess,json,hashlib,uuid
import numpy as np
from PIL import Image
from build_desk_substance import Graph,put

R=Path(__file__).resolve().parents[2];SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/tv_screen_imperfection';T=R/'02_assets/textures/generated/tv_screen_imperfection';C=R/'07_pipeline/cache/tv_screen_sd'
for p in (M,T,C):p.mkdir(parents=True,exist_ok=True)
g=Graph()
for el in (g.p,g.g):el.find('identifier').set('v','tv_screen_imperfection')
g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'tv-screen-layered-imperfection-20260916'))+'}')
g.g.find('./attributes/label').set('v','CRT glass / layered imperfections')
g.g.find('./attributes/description').set('v','Original native graph. Separate oil, dry deposits, curved wiping, fine scratches, crossed long scratches and clustered abrasion. One tile represents 0.8 m. No reference bitmap input or baked lighting.')
deposit_amount=g.expose('DepositAmount','Dry deposit coverage',.45,'01 Dirt',0,1)
oil_amount=g.expose('OilAmount','Oil film',.40,'01 Dirt',0,1)
wipe_amount=g.expose('WipeAmount','Curved cloth marks',.08,'02 Handling',0,1)
scratch_amount=g.expose('ScratchAmount','Fine scratch roughness',.38,'02 Handling',0,1)
long_amount=g.expose('LongScratchAmount','Sparse long scratches',.65,'02 Handling',0,1)
cross_amount=g.expose('CrossScratchAmount','Crossing fine scratches',.40,'02 Handling',0,1)
scuff_amount=g.expose('ScuffAmount','Localized abrasion',.20,'02 Handling',0,1)
base_r=g.expose('BaseRoughness','Clean glass roughness',.035,'03 Response',.01,.15)

def rotate(src,angle,x,y,offset=(0,0)):
    """Rotate/translate a grayscale layer using the installed native Transform graph."""
    return g.inst('Layer orientation / offset','safe_transform',x,y,{'input':src},{'rotation':('Float1',angle),'tile_safe_rotation':('Bool',0),'offset':('Float2',offset)},graph='safe_transform_grayscale')

def combine(bg,fg,amount,x,y,title):
    """Add white mask coverage without flattening the existing background detail."""
    return g.blend(title,bg,g.uniform('Mask contribution',1,x-260,y-170),x,y,fg,opacity=amount)

# Deposit shape and fine grains are independent: broad weathering never becomes a naked noise texture.
macro=g.inst('Uneven handling distribution','noise_bnw_spots_2',0,0,params={'scale':('Int1',2),'randomseed':('Int32',172)})
macro=g.inst('Soft contact pressure','blur_hq',300,0,{'Source':macro},{'Intensity':('Float1',10),'Quality':('Int1',1)},graph='blur_hq_grayscale')
patch=g.levels('Keep clean gaps between deposits',macro,600,0,.35,.62)
residue=g.inst('Fine irregular dried residue','grunge_spots_dirty',0,350,params={'balance':('Float1',.57),'contrast':('Float1',.24),'density':('Float1',.78),'scale':('Int1',5),'randomseed':('Int32',642)})
grains=g.inst('Fine distributed dust particles','noise_dirt_2',0,680,params={'scale':('Int1',9),'randomseed':('Int32',732)})
grains=g.levels('Isolate tiny dust grains',grains,320,680,.015,.45)
deposit=g.blend('Fine broken islands in the deposit field',residue,patch,900,350,mode=3)
swabs=deposit
deposit_core=g.inst('Broken dried film at millimetre scale','noise_dirt_4',600,630,params={'scale':('Int1',5),'randomseed':('Int32',492)})
deposit_core=g.levels('Separate dry flecks from thin film',deposit_core,880,630,.42,.78)
deposit=g.blend('Dry film only in handled regions',deposit_core,patch,1180,350,mode=3)
deposit=combine(deposit,grains,.15,1470,350,'Separate fine dust population')
deposit=combine(deposit,swabs,.08,1750,350,'Faint dried wipe residue among fine particles')

# Oil is a smooth thin film; dry residues and oil receive different reflectance values.
oil=g.inst('Independent finger handling film','noise_bnw_spots_2',0,1030,params={'scale':('Int1',3),'randomseed':('Int32',903)})
oil=g.inst('Soft oily boundaries','blur_hq',320,1030,{'Source':oil},{'Intensity':('Float1',16),'Quality':('Int1',1)},graph='blur_hq_grayscale')
oil=g.levels('Isolated pressure smears',oil,640,1030,.35,.60)
oil=rotate(oil,.13,940,1030,(.19,-.12))

# Cloth fibres curve across the screen and intersect a second diagonal wiping direction.
fibres=g.inst('Cloth micro striations','noise_anisotropic_noise',0,1450,params={'X_Amount':('Int1',640),'Y_Amount':('Int1',6),'smoothness':('Float1',.72),'randomseed':('Int32',340)})
bend=g.inst('Curvature variation','noise_clouds_2',0,1770,params={'scale':('Int1',2),'randomseed':('Int32',249)})
curved=g.filt('Curved fibres','warp',320,1450,{'input1':fibres,'inputgradient':bend},{'intensity':('Float1',.004)})
curved=rotate(curved,.18,620,1450)
# Local pressure and broken residue suppress uniform full-screen cloth stripes.
wipe_gate=g.levels('Local wipe pressure only',oil,650,1800,.40,.72)
curved=g.levels('Sparse surviving cloth fibres',curved,950,1450,.58,.90)
wipe=g.blend('Interrupted local wiping',curved,wipe_gate,1250,1450,mode=3)
wipe=g.blend('Broken cloth contact',wipe,patch,1530,1450,mode=3)

# Three different length populations prevent a repeated single-direction scratch pattern.
micro=g.inst('Fine straight abrasions','grunge_scratches_fine',0,2240,params={'balance':('Float1',.40),'contrast':('Float1',.62),'scratches_amount':('Float1',.65),'randomseed':('Int32',442)})
micro=g.levels('Isolate bright fine cuts from neutral background',micro,280,2240,.39,.80)
micro=g.inst('Shorten fine scratches to handling scale','safe_transform',560,2240,{'input':micro},{'tile':('Int1',3),'rotation':('Float1',.11),'tile_safe_rotation':('Bool',0)},graph='safe_transform_grayscale')
micro=g.blend('Interrupt fine cuts into local clusters',micro,patch,810,2240,mode=3)
long=g.inst('Sparse interrupted long cuts','grunge_scratches_rough',0,2570,params={'Position':('Float1',.38),'Contrast':('Float1',.65),'scratch_quantity':('Float1',.19),'scratch_width':('Float1',.08),'scratch_length':('Float1',.73),'scratch_masking':('Float1',.70),'double_scratch':('Float1',.10),'spots_opacity':('Float1',0),'dust':('Float1',0),'randomseed':('Int32',821)})
long=rotate(long,-.19,320,2570,(.12,.05))
cross=g.inst('Second independent fine abrasion direction','grunge_scratches_fine',0,2900,params={'balance':('Float1',.38),'contrast':('Float1',.66),'scratches_amount':('Float1',.38),'randomseed':('Int32',927)})
cross=g.levels('Sparse crossing cuts',cross,280,2900,.48,.90)
cross=rotate(cross,.34,580,2900,(-.17,.21))
scuff=g.blend('Local abrasion clusters',micro,oil,650,2240,mode=3)
scratches=combine(micro,long,long_amount,950,2450,'Fine plus long cuts')
scratches=combine(scratches,cross,cross_amount,1250,2450,'Intersecting abrasion directions')
scratches=combine(scratches,scuff,scuff_amount,1550,2450,'Localized scuff layer')

# Each visible phenomenon has its own roughness response; relief remains microscopic.
rr=g.uniform('Undisturbed clear glass',.035,1600,-100,base_r)
rr=g.blend('Dry dirt broadens reflections',rr,g.uniform('Dry film roughness',.40,1570,200),1900,0,deposit,opacity=deposit_amount)
rr=g.blend('Oil film response',rr,g.uniform('Oil roughness',.075,1870,600),2200,0,oil,opacity=oil_amount)
rr=g.blend('Cloth movement affects reflection',rr,g.uniform('Wiped roughness',.14,2180,900),2500,0,wipe,opacity=wipe_amount)
rr=g.blend('Scratches scatter the highlight',rr,g.uniform('Scratch roughness',.29,2480,1200),2800,0,scratches,opacity=scratch_amount)
hh=g.uniform('Neutral micro height',.5,1900,1800)
hh=g.blend('Minute deposited film relief',hh,g.uniform('Film height',.58,1900,2110),2200,1800,deposit,opacity=.28)
hh=g.blend('Fine cuts into the surface',hh,g.uniform('Scratch grooves',.25,2200,2110),2500,1800,scratches,opacity=.45)
outputs=[('DustMask',grains,None),('DepositMask',deposit,None),('OilMask',oil,None),('WipeMask',wipe,None),('MicroScratches',micro,None),('LongScratches',long,None),('ScuffMask',scuff,None),('ScratchMask',scratches,None),('Roughness',rr,'roughness'),('Height',hh,'height')]
for i,(name,src,usage) in enumerate(outputs):g.output(name,src,3200,i*310,usage)
# Arrange dependency columns with enough room for native nodes and separate comments.
original_nodes=list(g.nodes);depths={};columns={};new_labels=[]
for index,n in enumerate(original_nodes):
    uid=int(n.find('uid').get('v'))
    upstream=[int(c.find('connRef').get('v')) for c in n.findall('./connections/connection')]
    depth=max((depths.get(k,0)+1 for k in upstream),default=0);depths[uid]=depth
    row=columns.get(depth,0);columns[depth]=row+1
    x,y=depth*350,row*410
    n.find('./GUILayout/gpos').set('v',f'{x} {y} 0')
    if index<len(g.labels):new_labels.append((g.labels[index][0],x,y))
g.labels=new_labels
# Node names remain native; comments explain the layered construction.
for title,x,y in g.labels:
    q=put(g.gui,'GUIObject');put(q,'type','COMMENT');layout=put(q,'GUILayout');put(layout,'gpos',f'{x-70} {y-100} -100');put(layout,'size','245 58');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'frameColor','0.16 0.23 0.27 0.8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
E.indent(g.p);source=M/'tv_screen_imperfection.sbs';E.ElementTree(g.p).write(source,encoding='utf-8',xml_declaration=True)
commands=[[str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')],
    [str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(T),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
for i,cmd in enumerate(commands):
    with (C/f'sd_{i}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[]
for p in T.glob('*.png'):
    a=np.asarray(Image.open(p),dtype=float)/65535
    files.append({'file':p.relative_to(R).as_posix(),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean()),'p95':float(np.quantile(a,.95))})
report={'method':'Native editable Substance Designer graph / Adobe cooker and renderer','date':'2026-09-16','tile_m':.8,'bit_depth':16,'color_space':'Non-Color','nodes':len(g.nodes),'reference':'Sahaar Chhabra Retro CRT 90s Monitor / user supplied two screenshots; visual analysis only','seed':3087,'commands':commands,'files':files}
(T/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(files,indent=2))
