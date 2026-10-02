"""Author, cook and render editable Substance Designer architecture materials.

Fabric uses CC0 scanned yarns as image inputs, processed by native SD finishing nodes.
Other families use native generators. Previous Pillow maps are never used as SD inputs.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import sys, uuid, json, subprocess, hashlib
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from build_desk_substance import Graph,put
R=Path('D:/00_projects/10_CG/Shot_Test');SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/architecture_rebuild';T=R/'02_assets/textures/generated/architecture_sd';C=R/'07_pipeline/cache/architecture_rebuild'
M.mkdir(parents=True,exist_ok=True);T.mkdir(parents=True,exist_ok=True)

def input_image(g,name,color=False):
    """Declare a scanned source image input and return a correctly typed bridge."""
    pid=g.uid();p=put(g.inputs,'paraminput');put(p,'identifier',name);put(p,'uid',pid)
    put(put(p,'attributes'),'label',name);put(p,'isConnectable',1);put(p,'type',1 if color else 2)
    put(put(p,'defaultValue'),'constantValueFloat4' if color else 'constantValueFloat1','0.5 0.5 0.5 1' if color else .5)
    w=put(p,'defaultWidget');put(w,'name','');put(w,'options')
    n,h=g.node('CC0 ambientCG '+name,0,-450 if color else -200,1 if color else 2,{})
    b=put(put(n,'compImplementation'),'compInputBridge');put(b,'entry',pid);put(b,'parameters')
    return h

def save(g,name):
    """Save a distinct native SBS graph with normal node titles and explanatory frames."""
    for elem in [g.p.find('identifier'),g.g.find('identifier')]:elem.set('v','architecture_'+name)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'architecture_sd_'+name))+'}')
    g.g.find('./attributes/label').set('v','Architecture / '+name)
    g.g.find('./attributes/description').set('v','Real native Substance Designer graph. Fabric inputs: ambientCG Fabric030 CC0. Parameter values and source paths in adjacent manifest. No source photograph lighting baked into output. OpenGL normal, metres documented.')
    for label,x,y in g.labels:
        q=put(g.gui,'GUIObject');put(q,'type','COMMENT');ly=put(q,'GUILayout');put(ly,'gpos',f'{x-50} {y-90} -100');put(ly,'size','225 55');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',label);put(q,'frameColor','.18 .25 .23 .8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
    E.indent(g.p);p=M/f'architecture_{name}.sbs';E.ElementTree(g.p).write(p,encoding='utf-8',xml_declaration=True);return p

def build(name):
    """Return one graph plus native finish outputs, source input files and physical scale."""
    g=Graph();entries={};tile=.25;depth=.00008
    roughness={'linen':.81,'enamel':.39,'metal':.30,'glass':.038,'polymer':.68}[name]
    rp=g.expose('Roughness','Surface roughness',roughness,'Finish',.02,.95)
    age=g.expose('FinishVariation','Finish variation',.15,'Finish',0,.6)
    cloud=g.inst('Slow material response variation','noise_clouds_2',0,300,params={'scale':('Int1',5),'randomseed':('Int32',91126)})
    micro=g.inst('Submillimetre material texture','noise_perlin_noise',0,530,params={'scale':('Int1',420),'randomseed':('Int32',43)})
    scratch=g.inst('Sparse shallow handling scratches','grunge_scratches_fine',0,760,params={'balance':('Float1',.50),'contrast':('Float1',.35),'scratches_amount':('Float1',.07)})
    if name=='linen':
        tile=.25;depth=.00019
        src=R/'02_assets/textures/ambientcg/Fabric030/2k'
        entries={'ScanColor':src/'Fabric030_2K-JPG_Color.jpg','ScanHeight':src/'Fabric030_2K-JPG_Displacement.jpg','ScanRoughness':src/'Fabric030_2K-JPG_Roughness.jpg'}
        col=input_image(g,'ScanColor',True);ht=input_image(g,'ScanHeight');rr=input_image(g,'ScanRoughness')
        tint=g.expose('LinenPigment','Unbleached cotton-linen pigment',(.78,.74,.64,1),'Fabric',typ='Float4')
        tintnode=g.uniform('Warm cotton-linen pigment',(.78,.74,.64,1),400,-500,tint)
        bc=g.blend('Scanned yarn colour with neutral pigment',col,tintnode,750,-400,opacity=.52)
        # Uneven yarn thickness stays in the scan; weak native slubs add finish variation only.
        slub=g.inst('Natural longitudinal yarn irregularity','noise_directional_noise_1',400,250,params={'scale':('Int1',14),'angle':('Float1',0),'disorder':('Float1',.35)})
        ht=g.blend('Woven scan plus fine yarn irregularity',ht,slub,780,250,opacity=.06)
        ht=g.levels('Restrained fibre relief',ht,1020,250,outlow=.29,outhigh=.71)
        rough=g.blend('Natural fibre roughness',rr,g.uniform('Cotton surface roughness',.81,600,530,rp),1000,530,opacity=.72)
        # The map varies light transmission microscopically, not coarse alpha cut-outs.
        transmit=g.levels('Interstitial diffuse transmission',ht,1280,250,outlow=.31,outhigh=.19)
        g.output('Transmission',transmit,1920,1250,None)
    else:
        colors={'enamel':((.77,.75,.67,1),(.80,.78,.70,1)),'metal':((.70,.72,.70,1),(.73,.75,.73,1)),'glass':((.98,.99,.985,1),(.98,.99,.985,1)),'polymer':((.078,.081,.074,1),(.09,.093,.085,1))}
        lo,hi=colors[name];a=g.uniform('Material reflectance A',lo,300,-300);b=g.uniform('Material reflectance B',hi,300,-100)
        bc=g.blend('Subtle material colour variation',a,b,780,-200,cloud)
        if name=='metal':
            micro=g.inst('Fine parallel brushed aluminium','noise_anisotropic_noise',400,300,params={'X_Amount':('Int1',4),'Y_Amount':('Int1',640),'smoothness':('Float1',.82)})
            depth=.000018;tile=.20
        elif name=='glass':depth=.0000003;tile=1
        elif name=='polymer':depth=.000026
        ht=g.levels('Measured surface relief',micro,1000,250,outlow=.46,outhigh=.54)
        delta=.0007 if name=='glass' else .08
        rnoise=g.levels('Finish roughness range',micro,600,530,outlow=roughness-delta,outhigh=roughness+delta)
        rough=g.blend('Editable nominal roughness',g.uniform('Nominal surface roughness',roughness,600,740,rp),rnoise,1000,530,opacity=age)
        if name=='enamel':
            wear=g.levels('Selected shallow varnish scuff distribution',scratch,740,960,.45,.9,0,.027)
            ht=g.blend('Fine paint handling marks',ht,wear,1270,250,mode=2)
    normal=g.inst('Physical OpenGL normal','height_to_normal_world_units',1480,350,{'input':ht},{'surface_size':('Float1',tile*100),'height_depth':('Float1',depth*100),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    metallic=g.uniform('Material class',.82 if name=='metal' else 0,1250,800)
    for i,(n,h,u) in enumerate([('BaseColor',bc,'baseColor'),('Roughness',rough,'roughness'),('Height',ht,'height'),('Normal',normal,'normal'),('Metallic',metallic,'metallic')]):g.output(n,h,1920,i*220,u)
    return g,entries,tile,depth

rows=[]
for family in ['linen','enamel','metal','glass','polymer']:
    g,entries,tile,depth=build(family);source=save(g,family);dest=T/family;dest.mkdir(exist_ok=True)
    commands=[]
    cmd=[str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')]
    with (C/f'sd_{family}_cook.log').open('w',encoding='utf-8') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    commands.append(cmd)
    cmd=[str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report']
    for key,p in entries.items():cmd+=['--set-entry',key+'@'+str(p)]
    with (C/f'sd_{family}_render.log').open('w',encoding='utf-8') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    commands.append(cmd)
    files=[{'path':p.relative_to(R).as_posix(),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color','bit_depth':int(p.read_bytes()[24])} for p in dest.glob('*.png')]
    assert all(x['size']==[2048,2048] for x in files)
    row={'family':family,'source':source.relative_to(R).as_posix(),'sbsar':source.with_suffix('.sbsar').relative_to(R).as_posix(),'nodes':len(g.nodes),'tile_metres':tile,'height_range_metres':depth,'commands':commands,'inputs':[{ 'name':k,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':'https://ambientcg.com/view?id=Fabric030','license':'CC0'} for k,p in entries.items()],'files':files}
    rows.append(row);print('SD_NATIVE_COOK_RENDER',family,len(files),'maps',flush=True)
(T/'manifest.json').write_text(json.dumps({'date':'2026-09-11','authoring':'Editable native SD graphs, real local Adobe sbscooker and sbsrender exports. No Pillow maps used.','seed':91126,'normal':'OpenGL','materials':rows},indent=2),encoding='utf-8')
