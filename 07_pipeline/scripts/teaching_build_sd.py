"""Native Substance Designer teaching materials. SBS -> Adobe cooker -> Adobe render; no raster relabelling.
Wood uses existing CC0 scan inputs processed through coat/scratch/roughness nodes. Other families are native generators.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import uuid,subprocess,json,hashlib,sys
from PIL import Image
from build_desk_substance import Graph,put
R=Path('D:/00_projects/10_CG/Shot_Test');SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/teaching_rebuild';M.mkdir(parents=True,exist_ok=True)
T=R/'02_assets/textures/generated/teaching_sd';T.mkdir(parents=True,exist_ok=True)
C=R/'07_pipeline/cache/teaching_rebuild';rows=[]

def graph(name):
    """Input name; return a uniquely identified editable native SD graph."""
    g=Graph();g.p.find('identifier').set('v',name);g.g.find('identifier').set('v',name);g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'teaching_sd_'+name))+'}')
    g.g.find('./attributes/label').set('v',name);g.g.find('./attributes/description').set('v','Teaching native SD material. Photos are visual references only. Original native processing; explicit physical scale; OpenGL normals. Wood inputs are CC0 Poly Haven plywood; notice input is original nonsemantic artwork extracted from its old paper field.')
    return g

def input_image(g,name,color=True):
    """Input identifier/type; return externally editable image bridge for licensed scan or original artwork."""
    pid=g.uid();p=put(g.inputs,'paraminput');put(p,'identifier',name);put(p,'uid',pid);put(put(p,'attributes'),'label',name);put(p,'isConnectable',1);put(p,'type',1 if color else 2)
    put(put(p,'defaultValue'),'constantValueFloat4' if color else 'constantValueFloat1','0.5 0.5 0.5 1' if color else '0')
    w=put(p,'defaultWidget');put(w,'name','');put(w,'options');n,h=g.node(name+' input',-500,-700,1 if color else 2,{})
    b=put(put(n,'compImplementation'),'compInputBridge');put(b,'entry',pid);put(b,'parameters');return h

def finish(g,name,bc,rough,height,tile=.35,depth=.00015,extras=None,entry=None,size=11,normal_in=None,presets=None):
    """Save native graph, compile with Adobe cooker, export actual PBR images and record exact commands/hashes."""
    norm=g.inst('Physical OpenGL normal','height_to_normal_world_units',2100,950,{'input':height},{'surface_size':('Float1',tile*100),'height_depth':('Float1',depth*100),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    if normal_in:norm=g.inst('Scan normal plus coat scratches','normal_combine',2300,950,{'Input_1':normal_in,'Input':norm},{'blend_quality':('Int1',1)})
    outputs=[('BaseColor',bc,'baseColor'),('Roughness',rough,'roughness'),('Normal',norm,'normal'),('Height',height,'height'),('Metallic',g.uniform('Dielectric surface',0,1900,1300),'metallic')]+(extras or [])
    for i,(nm,h,usage) in enumerate(outputs):g.output(nm,h,2700,i*210,usage)
    for title,x,y in g.labels:
        q=put(g.gui,'GUIObject');put(q,'type','COMMENT');lay=put(q,'GUILayout');put(lay,'gpos',f'{x-60} {y-85} -100');put(lay,'size','210 50');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'frameColor','.18 .28 .22 .8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
    E.indent(g.p);p=M/(name+'.sbs');E.ElementTree(g.p).write(p,encoding='utf-8',xml_declaration=True)
    args=[str(SD/'sbscooker.exe'),'--inputs',str(p),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')]
    with (C/(name+'_cook.log')).open('w',encoding='utf-8') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
    for preset,inputs,params in presets or [(name,entry or {},{})]:
        dest=T/preset;dest.mkdir(exist_ok=True)
        cmd=[str(SD/'sbsrender.exe'),'render','--inputs',str(p.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value',f'$outputsize@{size},{size}','--engine','d3d11','--output-bit-depth','16','--no-report']
        for k,v in inputs.items():cmd+=['--set-entry',k+'@'+str(v)]
        for k,v in params.items():cmd+=['--set-value',k+'@'+str(v)]
        with (C/(preset+'_render.log')).open('w',encoding='utf-8') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        files=[{'path':f.relative_to(R).as_posix(),'size':list(Image.open(f).size),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'colorspace':'sRGB' if f.stem.endswith('BaseColor') else 'Non-Color'} for f in sorted(dest.glob('*.png'))]
        assert len(files)==len(outputs) and all(min(f['size'])>=2048 for f in files)
        rows.append({'family':preset,'source':p.relative_to(R).as_posix(),'sbsar':p.with_suffix('.sbsar').relative_to(R).as_posix(),'native_nodes':len(g.nodes),'inputs':{k:str(v) for k,v in inputs.items()},'parameters':params,'public_parameters':[a.find('identifier').get('v') for a in g.inputs],'tile_m':tile,'height_range_m':depth,'commands':[args,cmd],'files':files})
        (T/'manifest.json').write_text(json.dumps({'method':'Real native SBS authoring + Adobe cooker + sbsrender 16-bit outputs','seed':3087,'normal':'OpenGL','materials':rows},indent=2),encoding='utf-8')
        print('SD_RENDERED',preset,len(files),flush=True)

def wood():
    """Preserve scanned growth direction; SD adds finish breakup, fine scratches and a separate local edge-wear layer."""
    g=graph('teaching_varnished_wood');scan=input_image(g,'ScanColor');norm=input_image(g,'ScanNormal')
    wear=g.expose('Wear','Broken varnish edge coverage',.18,'Finish',0,1);rp=g.expose('Roughness','Varnish roughness',.31,'Finish',.1,.8)
    grain=g.inst('Coherent longitudinal wood fibres','wood_fibers_2',0,0)
    cloud=g.inst('Handled finish variation','noise_clouds_2',0,230,params={'scale':('Int1',3),'randomseed':('Int32',152)})
    scratch=g.inst('Fine cross-grain use scratches','grunge_scratches_fine',0,470,params={'balance':('Float1',.48),'contrast':('Float1',.72),'scratches_amount':('Float1',.18)})
    tint=g.uniform('Warm old clearcoat',(.72,.56,.36,1),330,-260);base=g.blend('Licensed scan beneath clearcoat',scan,tint,650,-200,mode=3)
    scuff=g.levels('Fine scratch mask',scratch,360,490,.55,.90)
    base=g.blend('Pale shallow handling scratches',base,g.uniform('Exposed dry birch',(.61,.51,.36,1),650,120),1000,-200,scuff,opacity=.11)
    rough=g.blend('Clearcoat controlled sheen',g.uniform('Base clearcoat roughness',.31,700,370,rp),g.levels('Handling sheen change',cloud,360,700,outlow=.31,outhigh=.50),1000,370,opacity=.36)
    rough=g.blend('Dull surface scuffs',rough,g.uniform('Exposed grain roughness',.63,850,620),1270,370,scuff,opacity=.30)
    height=g.levels('Fine pores',grain,350,930,outlow=.49,outhigh=.51);height=g.blend('Scratches cut clearcoat',height,g.levels('Shallow cut depth',scuff,650,930,outlow=0,outhigh=.028),1000,930,mode=2)
    shape=g.inst('Unworn centre of each face','shape',0,1200,params={'Size':('Float1',.992),'Pattern':('Int1',1)})
    border=g.levels('Geometric edge band',shape,300,1200,outlow=1,outhigh=0)
    broken=g.inst('Intermittent edge chips','histogram_scan',300,1440,{'Input_1':cloud},{'Position':wear,'Contrast':('Float1',.73)})
    edgemask=g.blend('Local edge wear placement',border,broken,650,1200,mode=3)
    raw=g.blend('Wood grain retained in worn areas',scan,g.uniform('Unsealed birch multiplier',(.90,.83,.68,1),700,1450),1000,1420,mode=3)
    extras=[('WearMask',edgemask,None),('ExposedBaseColor',raw,None),('ExposedRoughness',g.uniform('Dry wood roughness',.62,1300,1250),None)]
    p=R/'02_assets/textures/polyhaven/plywood/4k'
    finish(g,'teaching_varnished_wood',base,rough,height,.5,.00022,extras,{'ScanColor':p/'plywood_diff_4k.jpg','ScanNormal':p/'plywood_nor_gl_4k.png'},12,norm)

def chalkboard():
    """Native multiscale eraser streaks, broad curved wipes and mineral powder; no old bitmap input."""
    g=graph('teaching_chalkboard');amount=g.expose('ChalkResidue','Eraser residue',.27,'Board',0,.6)
    cloud=g.inst('Broad residual dust field','noise_clouds_2',0,0,params={'scale':('Int1',4),'randomseed':('Int32',154)})
    smudge=g.inst('Long erased bands','anisotropic_blur',300,0,{'Source':cloud},{'Intensity':('Float1',8),'Anisotropy':('Float1',.92),'Angle':('Float1',.25)},graph='anisotropic_blur_grayscale')
    bend=g.inst('Hand motion broad curvature','noise_clouds_2',0,260,params={'scale':('Int1',2),'randomseed':('Int32',168)})
    smudge=g.filt('Curving eraser sweeps','warp',550,0,{'input1':smudge,'inputgradient':bend},{'intensity':('Float1',.06)})
    fibre=g.inst('Fine felt wipe lines','noise_directional_scratches',0,520,params={'scale':('Int1',8),'angle':('Float1',.25),'angle_random':('Float1',.018),'pattern_amount':('Float1',.5)})
    powder=g.inst('Submillimetre chalk particles','noise_bnw_spots_2',0,760,params={'scale':('Int1',120)})
    residue=g.blend('Broad wipe plus fine felt striations',smudge,fibre,800,0,opacity=.14)
    residue=g.levels('Eraser contrast remap',residue,950,140,.42,.58,0,1)
    low=g.uniform('School board green',(.047,.161,.112,1),550,-270);high=g.uniform('Chalk residue reflectance',(.25,.31,.23,1),800,-270)
    bc=g.blend('Controlled blank board residue',low,high,1080,0,residue,opacity=amount)
    rough=g.levels('Chalk increases matte response',residue,1100,350,outlow=.64,outhigh=.79)
    height=g.levels('Paint tooth and powder film',powder,900,650,outlow=.495,outhigh=.51)
    height=g.blend('Thin chalk deposits',height,g.levels('Deposited powder depth',residue,650,900,outlow=.49,outhigh=.53),1200,650,opacity=.12)
    finish(g,'teaching_chalkboard',bc,rough,height,4.14,.00008,extras=[('ResidueMask',residue,None)],size=12)

def fibre_family(name,lo,hi,rough,depth,cloth=False,print_art=False):
    """Native cellulose or woven fibre surface; optional artwork is thresholded to ink before applying to new SD paper."""
    g=graph(name);a=g.expose('FibreStrength','Visible fibre contrast',.12,'Fibre',0,.5)
    fibres=g.inst('Interlocking fibres','fibers_1',0,0,params={'Tiling':('Int1',12 if cloth else 9)})
    micro=g.inst('Fine substrate tooth','noise_perlin_noise',0,250,params={'scale':('Int1',380)})
    cloud=g.inst('Very slight ageing','noise_clouds_2',0,500,params={'scale':('Int1',5)})
    signal=g.blend('Fibres embedded in smooth substrate',micro,fibres,350,0,opacity=.22 if cloth else .10)
    bc=g.blend('Natural uneven fibre reflectance',g.uniform('Substrate tint',lo,350,-300),g.uniform('Fibre tint',hi,600,-300),850,0,signal,opacity=a)
    bc=g.blend('Subtle handling stain',bc,g.uniform('Age stain',tuple(v*.91 if i<3 else v for i,v in enumerate(lo)),600,250),1100,0,cloud,opacity=.17)
    if print_art:
        art=input_image(g,'InkArtwork');gray=g.filt('Extract original graphic luminance','grayscaleconversion',300,-650,{'input1':art},channels=2)
        ink=g.levels('Discard former paper field; keep only ink',gray,650,-650,.30,.57,1,0)
        bc=g.blend('Faded nonsemantic print on new SD paper',bc,g.uniform('Aged printing ink',(.26,.27,.23,1),850,-650),1360,0,ink,opacity=.42)
    rr=g.levels('Fiber matte micro variation',signal,1100,350,outlow=rough-.035,outhigh=rough+.035)
    hh=g.levels('Microscopic fibre relief',signal,1100,650,outlow=.40,outhigh=.60)
    presets=None
    if print_art:presets=[(f'notice_{i:02}',{'InkArtwork':R/f'02_assets/textures/authored/teaching_rebuild/notice_{i:02}_color.png'},{}) for i in range(5)]
    finish(g,name,bc,rr,hh,.35,depth,presets=presets)

if __name__=='__main__':
    wood();chalkboard()
    fibre_family('teaching_paper',(.81,.785,.70,1),(.90,.88,.81,1),.78,.000045)
    fibre_family('teaching_bookcloth',(.30,.34,.28,1),(.38,.42,.35,1),.71,.000085,True)
    fibre_family('teaching_felt',(.13,.17,.14,1),(.21,.245,.20,1),.91,.00017,True)
    fibre_family('teaching_notices',(.81,.785,.70,1),(.90,.88,.81,1),.78,.000045,print_art=True)
