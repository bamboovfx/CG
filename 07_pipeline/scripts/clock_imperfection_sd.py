"""Author editable SD wiping/oil-film roughness; retain Blender's existing scratch branch.

Inputs: installed Adobe procedural nodes, visual reference by Zak Boxall.
Outputs: native SBS/SBSAR and 4K 16-bit data maps for a 40 cm tile.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import subprocess, json, hashlib, uuid
import numpy as np
from PIL import Image
from build_desk_substance import Graph, put

R=Path(__file__).resolve().parents[2]
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/clock_imperfection'
T=R/'02_assets/textures/generated/clock_imperfection'
C=R/'07_pipeline/cache/clock_imperfection'
for p in (M,T,C): p.mkdir(parents=True,exist_ok=True)
g=Graph()
for el in (g.p,g.g): el.find('identifier').set('v','clock_imperfection')
g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'clock-imperfection-v1'))+'}')
g.g.find('./attributes/label').set('v','Clock imperfection')
g.g.find('./attributes/description').set('v','40 cm tile. Local curved wiping and oil film in roughness only. Scratch height remains in Blender. Original native graph; references are not texture inputs.')
wipe_amount=g.expose('WipeAmount','Wipe amount',.65,'Surface',0,1)
oil_amount=g.expose('OilAmount','Oil amount',.55,'Surface',0,1)
base_r=g.expose('BaseRoughness','Base roughness',.37,'Surface',.2,.6)

# Long wiping strokes are bent coherently, then limited to scattered contact patches.
motion=g.inst('Cloth motion / fine parallel streaks','noise_anisotropic_noise',0,0,params={'X_Amount':('Int1',7),'Y_Amount':('Int1',320),'smoothness':('Float1',.8)})
bend=g.inst('Broad curvature of hand motion','noise_clouds_2',0,270,params={'scale':('Int1',2),'randomseed':('Int32',812)})
motion=g.filt('Curved wiping striations','warp',300,0,{'input1':motion,'inputgradient':bend},{'intensity':('Float1',.045)})
patch=g.inst('Contact islands','noise_bnw_spots_2',0,570,params={'scale':('Int1',2),'randomseed':('Int32',57)})
patch=g.inst('Elongated contact footprints','anisotropic_blur',300,570,{'Source':patch},{'Intensity':('Float1',16),'Anisotropy':('Float1',.92),'Angle':('Float1',.04)},graph='anisotropic_blur_grayscale')
patch=g.levels('Leave broad untouched enamel areas',patch,600,570,.43,.62)
patch=g.inst('Soft pressure falloff','blur_hq',890,570,{'Source':patch},{'Intensity':('Float1',2.5),'Quality':('Int1',1)},graph='blur_hq_grayscale')
striations=g.levels('Broken cloth fibres',motion,600,0,.25,.78,.12,1)
wipe=g.blend('Streaks only within wiping patches',patch,striations,1180,100,mode=3)

# Separate low-frequency oily contact film reduces roughness without embossing dirt.
oil=g.inst('Independent oil contact patches','noise_bnw_spots_2',0,920,params={'scale':('Int1',3),'randomseed':('Int32',919)})
oil=g.inst('Soft rubbed oil boundary','anisotropic_blur',300,920,{'Source':oil},{'Intensity':('Float1',12),'Anisotropy':('Float1',.85),'Angle':('Float1',.12)},graph='anisotropic_blur_grayscale')
oil=g.levels('Sparse handling film',oil,600,920,.48,.70)
oil=g.filt('Irregular hand smear contour','warp',890,920,{'input1':oil,'inputgradient':bend},{'intensity':('Float1',.022)})
oil=g.inst('Feathered film boundary','blur_hq',1180,920,{'Source':oil},{'Intensity':('Float1',3),'Quality':('Int1',1)},graph='blur_hq_grayscale')

# Finish values stay narrow; no 0–1 grunge signal is connected directly to roughness.
rr=g.uniform('Undisturbed satin enamel',.37,1200,-250,base_r)
rr=g.blend('Dry wipe slightly softens the highlight',rr,g.uniform('Dry wipe roughness',.45,1200,380),1490,0,wipe,opacity=wipe_amount)
rr=g.blend('Oil film slightly sharpens the highlight',rr,g.uniform('Oil film roughness',.28,1450,600),1780,0,oil,opacity=oil_amount)
grain=g.inst('Very fine coating texture','noise_perlin_noise',1200,1230,params={'scale':('Int1',250)})
grain=g.levels('Subtle manufacturing variation',grain,1490,1230,outlow=.355,outhigh=.385)
rr=g.blend('Micro response kept subordinate to wiping',rr,grain,2070,0,opacity=.08)
for i,(name,src,usage) in enumerate([('Roughness',rr,'roughness'),('WipeMask',wipe,None),('OilMask',oil,None)]): g.output(name,src,2400,i*330,usage)

# Comments explain stages while all nodes retain Adobe's default identities.
for title,x,y in g.labels:
 q=put(g.gui,'GUIObject');put(q,'type','COMMENT');layout=put(q,'GUILayout');put(layout,'gpos',f'{x-90} {y-100} -100');put(layout,'size','245 58');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'frameColor','0.16 0.23 0.27 0.8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
E.indent(g.p);source=M/'clock_imperfection.sbs';E.ElementTree(g.p).write(source,encoding='utf-8',xml_declaration=True)
commands=[ [str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')], [str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(T),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report'] ]
for i,cmd in enumerate(commands):
 with (C/f'sd_{i}.log').open('w') as log: subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[]
for p in T.glob('*.png'):
 a=np.asarray(Image.open(p),dtype=float)/65535
 files.append({'file':str(p.relative_to(R)),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'min':float(a.min()),'max':float(a.max()),'mean':float(a.mean()),'std':float(a.std()),'p95':float(np.quantile(a,.95))})
report={'method':'Native editable SD graph compiled/rendered by Adobe tools','tile_m':.4,'bit_depth':16,'colorspace':'Non-Color','nodes':len(g.nodes),'parameters':{'BaseRoughness':.37,'WipeAmount':.65,'OilAmount':.55},'references':[{'url':'https://zakboxall.artstation.com/blog/N0dE/making-realistic-materials-in-substance-steel-free-sample-textures','use':'Viewed imperfection moodboard and read artist breakdown; directional wiping, clean space, separate scratch scales. No artist image used as input.'},{'url':'https://www.adobe.com/learn/substance-3d-designer/web/mdl-malachite-material-breakdown','use':'Reference for separate smudge and fingerprint roughness masks.'}],'commands':commands,'files':files}
(T/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(files,indent=2))
