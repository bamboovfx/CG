"""在 SD 中制作课桌清漆木板与柜体纵向木纹；黑板保留原桌椅材质网络。"""
from pathlib import Path
import sys,uuid,json,hashlib,subprocess,xml.etree.ElementTree as E
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from build_desk_substance import Graph,put
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer');M=R/'02_assets/materials/wood_groups';T=R/'02_assets/textures/generated/wood_groups';C=R/'07_pipeline/cache/wood_groups'
for p in [M,T,C]:p.mkdir(parents=True,exist_ok=True)


def image_input(g,name):
    """添加真实 SD 图像输入，返回接口供 CC0 扫描底色参与原生处理。"""
    pid=g.uid();p=put(g.inputs,'paraminput');put(p,'identifier',name);put(p,'uid',pid)
    a=put(p,'attributes');put(a,'label',name);put(p,'isConnectable',1);put(p,'type',1)
    put(put(p,'defaultValue'),'constantValueFloat4','.5 .35 .2 1');w=put(p,'defaultWidget');put(w,'name','');put(w,'options')
    n,h=g.node(name,-400,0,1,{});b=put(put(n,'compImplementation'),'compInputBridge');put(b,'entry',pid);put(b,'parameters');return h


def build(family):
    """生成独立材质图及 4K 输出，写入可重现命令、尺度和来源。"""
    school=family=='school_board';g=Graph()
    for elem in [g.p,g.g]:elem.find('identifier').set('v',family)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'classroom-wood-'+family))+'}')
    g.g.find('./attributes/label').set('v',family)
    g.g.find('./attributes/description').set('v','Editable wood coating; 0.6m tile; 0.12mm height range; visual references are not texture sources.')
    contrast=g.expose('GrainContrast','Grain contrast',.23 if school else .67,'Wood',0,1)
    scratches=g.inst('Shallow clearcoat handling marks','grunge_scratches_fine',0,900)
    scratches=g.levels('Sparse handling scratches',scratches,250,900,.5,.9,0,1)
    fibre=g.inst('Fine directional wood fibres','wood_fibers_2' if school else 'wood_fibers_1',0,0,params={} if school else {'Disorder':('Float1',.43)})
    clouds=g.inst('Growth variation','noise_clouds_2',0,220,params={'scale':('Int1',2),'randomseed':('Int32',441 if school else 792)})
    grain=g.filt('Gently curved grain','warp',260,0,{'input1':fibre,'inputgradient':clouds},{'intensity':('Float1',.002 if school else .013)})
    if not school:
        fine=g.inst('Open pores and fine fibres','wood_fibers_2',260,190)
        grain=g.blend('Two scales of cabinet grain',grain,fine,500,120,opacity=.43)
    grain=g.levels('Grain contrast range',grain,500,0,.22,.78,.08,.92)
    low=(.48,.305,.16,1) if school else (.30,.19,.105,1)
    high=(.68,.49,.29,1) if school else (.57,.405,.235,1)
    base=g.blend('Wood body tone',g.uniform('Low grain tone',low,0,440),g.uniform('High grain tone',high,0,570),760,430,grain)
    if school:
        scan=image_input(g,'PlywoodColor')
        scan=g.filt('Align scanned grain with vertical fibres','transformation',0,-300,{'input1':scan},{'matrix22':('Float4',(0,1,-1,0))},channels=1)
        base=g.blend('Subtle scanned fibres below amber clearcoat',base,scan,1000,430,opacity=contrast)
    else:
        base=g.blend('Cabinet grain strength',g.uniform('Cabinet body',(.43,.29,.16,1),500,580),base,1000,430,opacity=contrast)
    rough=g.levels('Worn satin clearcoat',clouds,760,740,outlow=.35 if school else .42,outhigh=.53 if school else .62)
    rough=g.blend('Fine cuts scatter reflection',rough,g.uniform('Scratch roughness',.67,760,1020),1060,740,scratches,opacity=.15)
    height=g.levels('Coated wood microrelief',grain,760,1300,outlow=.46 if school else .35,outhigh=.54 if school else .65)
    height=g.blend('Hairline cut depth',height,g.uniform('Cut depth',.34,760,1510),1050,1300,scratches,opacity=.13)
    normal=g.inst('OpenGL normal at real scale','height_to_normal_world_units',1330,1300,{'input':height},{'surface_size':('Float1',60),'height_depth':('Float1',.012),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    for i,(name,value,usage) in enumerate([('BaseColor',base,'baseColor'),('Roughness',rough,'roughness'),('Height',height,'height'),('Normal',normal,'normal'),('Grain',grain,None),('ScratchMask',scratches,None)]):g.output(name,value,1650,i*230,usage)
    # Space native nodes by dependency depth; explanations remain separate comments.
    depths={};columns={};labels=[]
    for index,n in enumerate(g.nodes):
        uid=int(n.find('uid').get('v'));up=[int(c.find('connRef').get('v')) for c in n.findall('./connections/connection')]
        depth=max((depths.get(k,0)+1 for k in up),default=0);depths[uid]=depth;row=columns.get(depth,0);columns[depth]=row+1
        x,y=depth*360,row*410;n.find('./GUILayout/gpos').set('v',f'{x} {y} 0')
        if index<len(g.labels):labels.append((g.labels[index][0],x,y))
    for title,x,y in labels:
        q=put(g.gui,'GUIObject');put(q,'type','COMMENT');lay=put(q,'GUILayout');put(lay,'gpos',f'{x-50} {y-75} -100');put(lay,'size','240 45');put(q,'GUIName','');put(q,'uid',g.uid());put(q,'title',title);put(q,'isTitleVisible',1);put(q,'isFrameVisible',1)
    src=M/(family+'.sbs');E.indent(g.p);E.ElementTree(g.p).write(src,encoding='utf-8',xml_declaration=True)
    dest=T/family;dest.mkdir(exist_ok=True)
    commands=[[str(SD/'sbscooker.exe'),'--inputs',str(src),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')],[str(SD/'sbsrender.exe'),'render','--inputs',str(src.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]
    if school:commands[1]+=['--set-entry','PlywoodColor@'+str(R/'02_assets/textures/polyhaven/plywood/4k/plywood_diff_4k.jpg')]
    for i,cmd in enumerate(commands):
        with (C/(family+str(i)+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    record={'family':family,'source':str(src.relative_to(R)),'tile_metres':.6,'height_range_m':.00012,'normal':'OpenGL','commands':commands,'seed':3087,'nodes':len(g.nodes),'reference_use':'Visual research only','scan_source':'https://polyhaven.com/a/plywood' if school else None,'scan_license':'CC0' if school else None,'files':[{'path':str(p.relative_to(R)),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color'} for p in dest.glob('*.png')]}
    print('SD_READY',family,flush=True);return record


records=[build(f) for f in ['school_board','cabinet_wood']]
(T/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
