"""Build genuine native Substance Designer graphs for classroom equipment material families.
Inputs are native Adobe generators plus CC0 Poly Haven scans for wood; every output is genuinely processed by SD.
Each source stays editable, with separate grain, coat, handling scratches and measured normal branches.
"""
from pathlib import Path
import sys,xml.etree.ElementTree as E,uuid,subprocess,json,hashlib
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from build_desk_substance import Graph,put
ROOT=Path('D:/00_projects/10_CG/Shot_Test');SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer');OUT=ROOT/'02_assets/materials/equipment_rebuild';OUT.mkdir(parents=True,exist_ok=True)
TEX=ROOT/'02_assets/textures/generated/equipment_sd';TEX.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'07_pipeline/cache/equipment_rebuild';manifest=[]
FAMILIES={'varnished_wood':((.48,.31,.15,1),(.69,.54,.33,1),.38,0,.00013),'exposed_wood':((.56,.44,.28,1),(.74,.65,.46,1),.69,0,.00020),'abs':((.365,.39,.345,1),(.395,.425,.37,1),.48,0,.000026),'enamel':((.69,.67,.59,1),(.73,.70,.62,1),.43,0,.000022),'metal':((.58,.60,.56,1),(.63,.65,.60,1),.34,.85,.000018),'rubber':((.06,.066,.057,1),(.085,.093,.08,1),.73,0,.00003),'glass':((.24,.28,.25,1),(.245,.287,.257,1),.16,0,.000003),'paper':((.82,.80,.71,1),(.85,.83,.75,1),.67,0,.000015),'dark':((.085,.091,.079,1),(.10,.107,.095,1),.54,0,.000020)}

def save_graph(g,name):
    """Write the editable native source with default node identities and separate comment frames."""
    g.p.find('identifier').set('v','equipment_'+name);g.g.find('identifier').set('v','equipment_'+name);g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'equipment_sd_'+name))+'}')
    g.g.find('./attributes/label').set('v','Equipment / '+name)
    g.g.find('./attributes/description').set('v','Native SD generators; 0.25 metre tile; original material research; public roughness and scratch controls. No baked lighting or bitmap re-labelling.')
    for title,x,y in g.labels:
        q=put(g.gui,'GUIObject');put(q,'type','COMMENT');lay=put(q,'GUILayout');put(lay,'gpos',f'{x-70} {y-90} -100');put(lay,'size','220 52');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'frameColor','0.19 0.25 0.27 0.8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
    E.indent(g.p);p=OUT/('equipment_'+name+'.sbs');E.ElementTree(g.p).write(p,encoding='utf-8',xml_declaration=True);return p

def scan_input(g,name,channels,x,y):
    """Expose an actual native image input; source file bindings are recorded in SAT render commands."""
    pid=g.uid();p=put(g.inputs,'paraminput');put(p,'identifier',name);put(p,'uid',pid);a=put(p,'attributes');put(a,'label',name);put(a,'description','CC0 Poly Haven plywood 4K source. Bind the source path listed in manifest.json / render command.');put(p,'isConnectable',1);put(p,'type',channels);put(put(p,'defaultValue'),'constantValueFloat4' if channels==1 else 'constantValueFloat1','0.4 0.3 0.2 1' if channels==1 else '.5')
    w=put(p,'defaultWidget');put(w,'name','');put(w,'options');n,h=g.node('CC0 scan / '+name,x,y,channels,{})
    b=put(put(n,'compImplementation'),'compInputBridge');put(b,'entry',pid);put(b,'parameters');return h

for family,(lo,hi,rough,metal,depth) in FAMILIES.items():
    if len(sys.argv)>1 and family not in sys.argv[1:]:continue
    g=Graph();rp=g.expose('Roughness','Clearcoat / surface roughness',rough,'Surface',.05,.9);sp=g.expose('ScratchAmount','Handling scratch amount',.11 if family=='varnished_wood' else .025,'Surface',0,.5)
    low=g.uniform('Material low tone',lo,0,400);high=g.uniform('Material high tone',hi,0,550)
    if 'wood' in family:
        # Native wood fibres plus low-frequency directional warp retain coherent growth direction.
        signal=g.inst('Longitudinal wood fibres','wood_fibers_2',0,0)
        cloud=g.inst('Slow growth variation','noise_clouds_2',0,180,params={'scale':('Int1',2)})
        signal=g.filt('Gently curved wood fibres','warp',240,0,{'input1':signal,'inputgradient':cloud},{'intensity':('Float1',.003)})
        grain=g.levels('Wood fibre contrast',signal,470,0,.12,.88,.10,.9)
    elif family=='metal':
        signal=g.inst('Rolled steel directional microtexture','noise_anisotropic_noise',0,0,params={'X_Amount':('Int1',6),'Y_Amount':('Int1',512),'smoothness':('Float1',.7)})
        grain=g.levels('Restrained rolling contrast',signal,470,0,0,1,.25,.75)
    else:
        signal=g.inst('Fine moulded surface texture','noise_clouds_2',0,0,params={'scale':('Int1',9)})
        grain=g.levels('Subtle surface variation',signal,470,0,0,1,.25,.75)
    scratches=g.inst('Clearcoat handling micro scratches','grunge_scratches_fine',0,780,params={'balance':('Float1',.48),'contrast':('Float1',.36),'scratches_amount':sp})
    base=g.blend('Material colour from fibres',low,high,700,420,mask=grain)
    roughbase=g.uniform('Controlled roughness',rough,700,700,exposed=rp)
    roughnoise=g.levels('Light scratch polish contrast',scratches,490,800,0,1,max(.05,rough-.08),min(.95,rough+.08))
    rout=g.blend('Micro scratches in clearcoat roughness',roughbase,roughnoise,960,720,opacity=.3)
    h=g.levels('Measured microscopic relief',grain,710,1000,0,1,.34,.66)
    if family=='varnished_wood':h=g.blend('Clearcoat hairline relief',h,scratches,970,1000,opacity=.045)
    normal=g.inst('Normal from physical centimetres','height_to_normal_world_units',1220,1000,{'input':h},{'surface_size':('Float1',60 if 'wood' in family else 25),'height_depth':('Float1',depth*100),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    entries={}
    if 'wood' in family:
        scan=scan_input(g,'WoodColorScan',1,-350,1900);sr=scan_input(g,'WoodRoughScan',2,-350,2080);sn=scan_input(g,'WoodNormalScan',1,-350,2260)
        base=g.blend('Real broad growth grain with subtle native fibre layer',scan,base,1150,430,opacity=.16 if family=='varnished_wood' else .45)
        # Amber absorption is a coating layer; exposed wood keeps its paler original scan colour.
        if family=='varnished_wood':base=g.blend('Amber varnish absorption',base,g.uniform('Aged transparent amber coating',(.83,.70,.48,1),850,1880),1370,430,mode=3)
        rout=g.blend('Clearcoat over measured timber roughness',rout,sr,1150,730,opacity=.16 if family=='varnished_wood' else .42)
        normal=g.blend('Subdued scanned pores beneath coating',normal,sn,1450,1020,opacity=.22 if family=='varnished_wood' else .65)
        source_dir=ROOT/'02_assets/textures/polyhaven/plywood/4k'
        entries={'WoodColorScan':source_dir/'plywood_diff_4k.jpg','WoodRoughScan':source_dir/'plywood_rough_4k.jpg','WoodNormalScan':source_dir/'plywood_nor_gl_4k.png'}
    metall=g.uniform('Metallic physical class',metal,960,1300);ao=g.uniform('No baked lighting AO',1,960,1440)
    wear=g.levels('Directional wear breakup',scratches,700,1550,.3,.8,0,1)
    for i,(nm,src,usage) in enumerate([('BaseColor',base,'baseColor'),('Roughness',rout,'roughness'),('Metallic',metall,'metallic'),('Height',h,'height'),('Normal',normal,'normal'),('AO',ao,'ambientOcclusion'),('WearMask',wear,None)]):g.output(nm,src,1500,200+i*180,usage)
    source=save_graph(g,family)
    commands=[]
    args=[str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(OUT),'--alias','sbs://'+str(SD/'resources/packages')]
    with (CACHE/f'sd_{family}_cook.log').open('w',encoding='utf-8') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
    commands.append(args);dest=TEX/family;dest.mkdir(exist_ok=True)
    args=[str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report']
    for key,path in entries.items():args+=['--set-entry',key+'@'+str(path)]
    with (CACHE/f'sd_{family}_render.log').open('w',encoding='utf-8') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
    commands.append(args)
    files=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color'} for p in dest.glob('*.png')]
    manifest.append({'family':family,'source':source.relative_to(ROOT).as_posix(),'sbsar':source.with_suffix('.sbsar').relative_to(ROOT).as_posix(),'native_nodes':len(g.nodes),'public_parameters':['Roughness','ScratchAmount']+list(entries),'tile_metres':.6 if entries else .25,'source_grain_axis':'U' if entries else 'V','input_images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'license':'CC0','source_url':'https://polyhaven.com/a/plywood'} for p in entries.values()],'height_range_metres':depth,'normal_convention':'OpenGL','seed':3087,'license':'Original authored native graph; Adobe installed procedural node dependencies compiled with licensed local tools; wood uses CC0 Poly Haven scans','commands':commands,'files':files})
    print('COOKED AND RENDERED',family,len(files),flush=True)
if len(sys.argv)>1:
    old=json.loads((TEX/'manifest.json').read_text());manifest=[x for x in old if x['family'] not in sys.argv[1:]]+manifest
(TEX/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

