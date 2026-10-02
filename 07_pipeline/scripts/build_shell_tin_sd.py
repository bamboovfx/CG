"""Author native SD material families for parquet, plaster and printed tin.

Inputs: Adobe native procedural nodes, existing original label artwork.
Outputs: editable SBS, cooked SBSAR and traceable 2K/4K PBR maps.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import subprocess,json,hashlib,uuid
from PIL import Image
from build_desk_substance import Graph,put
R=Path(__file__).resolve().parents[2]
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=R/'02_assets/materials/shell_tin_rebuild';M.mkdir(parents=True,exist_ok=True)
T=R/'02_assets/textures/generated/shell_tin_sd';T.mkdir(parents=True,exist_ok=True)
C=R/'07_pipeline/cache/shell_tin_rebuild';C.mkdir(parents=True,exist_ok=True)

def graph(name):
    """Create a native graph with unique package identity; return editable Graph."""
    g=Graph();g.p.find('identifier').set('v',name);g.g.find('identifier').set('v',name)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,name))+'}')
    g.g.find('./attributes/label').set('v',name)
    g.g.find('./attributes/description').set('v','Native SD material, film dro:p reference. No baked lighting. Parameters and physical normals exposed. Reference photographs are not used as material maps.')
    return g

def color_input(g,name):
    """Declare original artwork input, RGB, and return bridge handle."""
    pid=g.uid();p=put(g.inputs,'paraminput');put(p,'identifier',name);put(p,'uid',pid)
    put(put(p,'attributes'),'label',name);put(p,'isConnectable',1);put(p,'type',1)
    put(put(p,'defaultValue'),'constantValueFloat4','0.35 0.035 0.02 1')
    w=put(p,'defaultWidget');put(w,'name','');put(w,'options')
    n,h=g.node('Original print design',0,-500,1,{})
    b=put(put(n,'compImplementation'),'compInputBridge');put(b,'entry',pid);put(b,'parameters')
    return h

def finish(g,name,bc,rough,height,metal,size=11,entry=None,tilecm=30,depthcm=.02,scan_normal=None):
    """Save, cook and render one native graph; return exported file records."""
    normal=g.inst('OpenGL physical normal','height_to_normal_world_units',2200,900,{'input':height},{'surface_size':('Float1',tilecm),'height_depth':('Float1',depthcm),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    if scan_normal:normal=g.inst('Scan grain plus SD wear normal','normal_combine',2400,900,{'Input_1':scan_normal,'Input':normal},{'blend_quality':('Int1',1)})
    for i,(n,h,u) in enumerate([('BaseColor',bc,'baseColor'),('Roughness',rough,'roughness'),('Height',height,'height'),('Metallic',metal,'metallic'),('Normal',normal,'normal')]):g.output(n,h,2600,i*240,u)
    for label,x,y in g.labels:
        q=put(g.gui,'GUIObject');put(q,'type','COMMENT');lay=put(q,'GUILayout');put(lay,'gpos',f'{x-50} {y-80} -100');put(lay,'size','180 48');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',label);put(q,'frameColor','.20 .26 .24 .8');put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
    E.indent(g.p);path=M/(name+'.sbs');E.ElementTree(g.p).write(path,encoding='utf8',xml_declaration=True)
    dest=T/name;dest.mkdir(exist_ok=True)
    cmd=[str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')]
    with (C/(name+'_cook.log')).open('w',encoding='utf8') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    cmd=[str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value',f'$outputsize@{size},{size}','--engine','d3d11','--output-bit-depth','16','--no-report']
    if entry:
        for key,value in (entry.items() if isinstance(entry,dict) else [('Artwork',entry)]):cmd+=['--set-entry',key+'@'+str(value)]
    with (C/(name+'_render.log')).open('w',encoding='utf8') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    records=[{'file':p.relative_to(R).as_posix(),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color'} for p in sorted(dest.glob('*.png'))]
    assert len(records)==5 and all(x['size']==[2**size]*2 for x in records)
    print('SD_RENDERED',name,flush=True)
    return {'name':name,'source':path.relative_to(R).as_posix(),'sbsar':path.with_suffix('.sbsar').relative_to(R).as_posix(),'nodes':len(g.nodes),'tile_cm':tilecm,'height_range_cm':depthcm,'input_artwork':str(entry) if entry else None,'outputs':records}

def wood():
    """Build directional fibers and fractured wax sheen, with separate wear masks."""
    g=graph('parquet_varnished_oak')
    a=g.expose('Wear','Varnish wear',.32,'Finish',0,1)
    fib=g.inst('Long oak fibers','wood_fibers_1',0,0,params={'Disorder':('Float1',.27),'randomseed':('Int32',152)})
    pores=g.inst('Fine vascular grain','wood_fibers_2',0,260,params={'randomseed':('Int32',43)})
    cloud=g.inst('Polished and dull handling zones','noise_clouds_2',0,520,params={'scale':('Int1',3),'randomseed':('Int32',152)})
    scratches=g.inst('Fine dragging scratches','grunge_scratches_fine',0,780,params={'balance':('Float1',.48),'contrast':('Float1',.6),'scratches_amount':('Float1',.25)})
    wear=g.inst('Discontinuous lacquer loss','histogram_scan',300,520,{'Input_1':cloud},{'Position':a,'Contrast':('Float1',.55)})
    grain=g.blend('Multiscale oak grain',fib,pores,300,0,opacity=.22)
    dark=g.uniform('Oak latewood',(.28,.18,.095,1),500,-300)
    light=g.uniform('Honey brown earlywood',(.49,.36,.22,1),500,-100)
    scan=color_input(g,'WoodColor');normal=color_input(g,'WoodNormal')
    bc=g.blend('Scan grain under warm varnish',scan,g.uniform('Walnut clear finish',(.57,.43,.27,1),700,-500),750,0,mode=3)
    dry=g.uniform('Exposed pale wood',(.55,.43,.29,1),750,300)
    bc=g.blend('Restrained coating desaturation',bc,dry,1000,0,wear,opacity=.19)
    rough0=g.levels('Wax sheen',cloud,500,550,outlow=.22,outhigh=.32)
    rough1=g.levels('Worn clear coat',scratches,500,780,outlow=.41,outhigh=.57)
    rough=g.blend('Lacquer reflection breakup',rough0,rough1,1100,550,wear)
    ht=g.levels('Pores under clear coat',grain,500,1050,outlow=.48,outhigh=.52)
    cut=g.levels('Microscratches in varnish',scratches,800,1050,outlow=0,outhigh=.028)
    ht=g.blend('Shallow grooves',ht,cut,1100,1050,mode=2)
    source=R/'02_assets/textures/polyhaven/plywood/4k'
    return finish(g,'parquet_varnished_oak',bc,rough,ht,g.uniform('Dielectric',0,1700,550),12,entry={'WoodColor':source/'plywood_diff_4k.jpg','WoodNormal':source/'plywood_nor_gl_4k.png'},tilecm=60,depthcm=.04,scan_normal=normal)

def plaster():
    """Build roller stipple over fine plaster, with controlled non-directional age."""
    g=graph('painted_school_plaster')
    tint=g.expose('Paint','Wall paint',(.57,.59,.48,1),'Pigment',typ='Float4')
    cloud=g.inst('Slow pigment aging','noise_clouds_2',0,0,params={'scale':('Int1',3)})
    micro=g.inst('Roller stipple','noise_perlin_noise',0,250,params={'scale':('Int1',240)})
    pores=g.inst('Mineral pits','noise_bnw_spots_2',0,500,params={'scale':('Int1',30)})
    bc=g.uniform('Paint pigment',(.57,.59,.48,1),300,-200,tint)
    dark=g.uniform('Subtle embedded age',(.49,.51,.40,1),300,0)
    bc=g.blend('Uneven age',bc,dark,700,0,cloud,opacity=.11)
    rough=g.levels('Matte mineral surface',micro,600,350,outlow=.66,outhigh=.78)
    ht=g.blend('Plaster plus roller',micro,pores,500,650,opacity=.22)
    ht=g.levels('Submillimetre relief',ht,900,650,outlow=.43,outhigh=.57)
    return finish(g,'painted_school_plaster',bc,rough,ht,g.uniform('Dielectric',0,1400,400),11,tilecm=60,depthcm=.06)

def tin(name,print_layer=False,red_layer=False):
    """Build oxidized tinplate or worn original lithographic artwork via native graph."""
    g=graph(name)
    cloud=g.inst('Handled surface','noise_clouds_2',0,0,params={'scale':('Int1',3),'randomseed':('Int32',168)})
    scratch=g.inst('Fine scratches','grunge_scratches_fine',0,240,params={'balance':('Float1',.5),'contrast':('Float1',.65)})
    flake=g.inst('Small finish abrasions','noise_bnw_spots_2',0,480,params={'scale':('Int1',8),'randomseed':('Int32',31)})
    flake=g.levels('Rare chips',flake,300,480,.76,.91)
    silver=g.uniform('Tin reflectance',(.66,.68,.66,1),500,-250)
    oxide=g.uniform('Mottled tin oxide',(.36,.38,.34,1),500,-70)
    bc=g.blend('Aged tinplate',silver,oxide,800,-70,cloud,opacity=.23)
    rough=g.levels('Handled tin sheen',scratch,700,270,outlow=.27,outhigh=.42)
    metal=g.uniform('Conductive tin',.96,1600,400)
    if print_layer or red_layer:
        art=color_input(g,'Artwork') if print_layer else g.uniform('Red lithographic lacquer',(.37,.028,.014,1),200,-500)
        bc=g.blend('Print wear revealing metal',art,bc,1150,-70,flake)
        metal=g.levels('Only exposed metal conducts',flake,1400,400,outlow=0,outhigh=.96)
        rough=g.blend('Ink and exposed tin',g.uniform('Lithographic ink',.42,650,650),rough,1150,270,flake)
    ht=g.levels('Shallow stamping microrelief',scratch,1000,800,outlow=.485,outhigh=.515)
    entry=next((R/'02_assets/textures').rglob('tin_label_color_2k.png')) if print_layer else None
    return finish(g,name,bc,rough,ht,metal,11,entry,tilecm=12,depthcm=.007)

if __name__=='__main__':
    rows=[wood(),plaster(),tin('aged_tinplate'),tin('printed_candy_tin',True),tin('red_candy_lacquer',red_layer=True)]
    (T/'manifest.json').write_text(json.dumps({'date':'2026-09-11','authoring':'Substance Designer native graphs; real Adobe cooker/render exports','normal':'OpenGL','seed':152,'materials':rows},indent=2),encoding='utf8')
