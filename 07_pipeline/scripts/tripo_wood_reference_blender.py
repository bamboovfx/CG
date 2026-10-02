"""将分层木材应用到Tripo课椅；输入最新候选和SD贴图，输出独立工程及评审。

保留顶点、三角面、既有UV、自定义法线和五金材质；新增木板专用投影UV。
"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
# Blender的脚本入口不自动把同目录放入模块搜索路径。
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import node, socket, frame, math_node, mix, aim

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_baked.blend'
WORK=ROOT/'07_pipeline/cache/tripo_wood_reference_20260930'
OUT=ROOT/'06_review/tripo_wood_reference_20260930'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_reference'
PARAMS={'Scratches':.90,'Age':.22,'Wear':.75}


def color(value):
    """输入SD中的sRGB三通道颜色，返回Blender线性RGBA。"""
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in value)+(1,)


def texture(tree, board, channel, vector, x=0, y=0):
    """输入木板、SD通道和坐标，返回打包且颜色空间正确的纹理接口。"""
    n=node(tree,'ShaderNodeTexImage',channel,x,y)
    n.image=bpy.data.images.load(str(TEX/board/(channel+'.png')),check_existing=True)
    n.image.colorspace_settings.name='sRGB' if 'BaseColor' in channel else 'Non-Color'
    n.image.pack(); n.extension='EXTEND'; tree.links.new(vector,n.inputs['Vector'])
    return n.outputs['Color']


def process(board):
    """输入木板标识，返回五通道工艺层组；方向由专用木板UV定义。"""
    g=bpy.data.node_groups.new('Wood / 工艺层 / Reference '+board,'ShaderNodeTree')
    socket(g,'Vector','NodeSocketVector')
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Metallic','NodeSocketFloat'),('Normal','NodeSocketVector'),('AO','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-850,0); o=node(g,'NodeGroupOutput','output',450,0)
    for k,(channel,target) in enumerate([('BaseColor','Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal'),('AO','AO')]):
        signal=texture(g,board,'Process_'+channel,i.outputs['Vector'],-500,450-k*220)
        if target=='Normal':
            normal=node(g,'ShaderNodeNormalMap','process_normal',0,-250)
            normal.uv_map='UV_WoodReference'; normal.inputs['Strength'].default_value=1.0
            if hasattr(normal,'convention'): normal.convention='OPENGL'
            g.links.new(signal,normal.inputs['Color']); signal=normal.outputs['Normal']
        g.links.new(signal,o.inputs[target])
    frame(g,'工艺层：宽幅生长纹／蜜色涂层／顺纹微细节；AO独立',[n for n in g.nodes if n.type not in {'GROUP_INPUT','GROUP_OUTPUT','FRAME'}])
    return g


def appearance(board):
    """输入木板标识，返回定向划痕、老化、窄边磨损及背面印记组。"""
    g=bpy.data.node_groups.new('Wood / 表现层 / Reference '+board,'ShaderNodeTree')
    for name,kind in [('Vector','NodeSocketVector'),('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Rear','NodeSocketFloat')]: socket(g,name,kind)
    for name,value in PARAMS.items(): socket(g,name,'NodeSocketFloat',default=value)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Coat','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-1550,0); o=node(g,'NodeGroupOutput','output',2100,0)
    masks={}
    for k,(channel,param) in enumerate([('ScratchDark','Scratches'),('ScratchLight','Scratches'),('AgeMask','Age'),('WearMask','Wear')]):
        signal=texture(g,board,channel,i.outputs['Vector'],-1200,780-k*260)
        masks[channel]=math_node(g,'MULTIPLY',signal,i.outputs[param],-890,780-k*260)
    c=mix(g,i.outputs['Color'],color((.39,.24,.09)),masks['AgeMask'],'aged_color',-350,650)
    c=mix(g,c,color((.64,.49,.28)),masks['WearMask'],'exposed_wood',0,650)
    c=mix(g,c,color((.17,.075,.021)),masks['ScratchDark'],'dark_grooves',350,650)
    c=mix(g,c,color((.65,.48,.24)),masks['ScratchLight'],'light_scuffs',700,650)
    stamp=texture(g,board,'StampMask',i.outputs['Vector'],-1200,-450)
    stamp=math_node(g,'MULTIPLY',stamp,i.outputs['Rear'],-890,-450)
    stamp=math_node(g,'MULTIPLY',stamp,i.outputs['Age'],-620,-450)
    c=mix(g,c,color((.18,.08,.025)),math_node(g,'MULTIPLY',stamp,3,-300,-450),'worn_imprint',1050,650)
    rough=mix(g,i.outputs['Roughness'],.47,masks['AgeMask'],'age_rough',-350,290)
    rough=mix(g,rough,.64,masks['WearMask'],'wear_rough',0,290)
    scratches=math_node(g,'MAXIMUM',masks['ScratchDark'],masks['ScratchLight'],0,-150)
    rough=mix(g,rough,.62,scratches,'scratch_rough',700,290)
    bump=node(g,'ShaderNodeBump','scratch_grooves',1050,-100)
    bump.inputs['Distance'].default_value=.000055; bump.inputs['Strength'].default_value=.45
    g.links.new(math_node(g,'SUBTRACT',0,scratches,650,-180),bump.inputs['Height'])
    g.links.new(i.outputs['Normal'],bump.inputs['Normal'])
    coat=math_node(g,'MULTIPLY',.12,math_node(g,'SUBTRACT',1,masks['WearMask'],1150,300),1510,300)
    for name,signal in [('Color',c),('Roughness',rough),('Normal',bump.outputs['Normal']),('Coat',coat)]: g.links.new(signal,o.inputs[name])
    frame(g,'表现层：交叉长划痕／暖色老化／窄边缺口；背面印记单独限位',[n for n in g.nodes if n.type not in {'GROUP_INPUT','GROUP_OUTPUT','FRAME'}])
    return g


def face_material(board):
    """输入木板标识，返回两组分层材质及其效果强度控制节点。"""
    m=bpy.data.materials.new('Reference wood / '+board); m.use_nodes=True; t=m.node_tree
    p=t.nodes.get('Principled BSDF'); out=t.nodes.get('Material Output'); p.location=(800,150); out.location=(1150,150)
    uv=node(t,'ShaderNodeUVMap','board_projection',-900,250); uv.uv_map='UV_WoodReference'
    proc=node(t,'ShaderNodeGroup','process',-600,250); proc.node_tree=process(board)
    app=node(t,'ShaderNodeGroup','appearance',-50,250); app.node_tree=appearance(board)
    for group in (proc,app): t.links.new(uv.outputs['UV'],group.inputs['Vector'])
    for channel in ('Color','Roughness','Normal'): t.links.new(proc.outputs[channel],app.inputs[channel])
    rear=node(t,'ShaderNodeAttribute','rear_only',-580,-300); rear.attribute_name='reference_rear'; t.links.new(rear.outputs['Fac'],app.inputs['Rear'])
    for source,target in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Coat','Coat Weight')]: t.links.new(app.outputs[source],p.inputs[target])
    # 旧涂层也跟随木孔结构，避免清漆使用恒定反射与几何法线。
    t.links.new(app.outputs['Normal'],p.inputs['Coat Normal'])
    t.links.new(app.outputs['Roughness'],p.inputs['Coat Roughness'])
    t.links.new(proc.outputs['Metallic'],p.inputs['Metallic']); p.inputs['Coat Roughness'].default_value=.35
    frame(t,'工艺层：木板专用UV，宽幅纹与细纤维同向',[uv,proc])
    frame(t,'表现层：三个独立强度，背面印记限位',[app,rear])
    m['wood_reference_board']=board; m.asset_mark(); return m,app


def edge_material(axis):
    """输入厚度轴，返回独立层压截面材质；不把面纹拉到侧面。"""
    m=bpy.data.materials.new('Reference wood / plywood edge'); m.use_nodes=True; t=m.node_tree
    p=t.nodes.get('Principled BSDF'); p.inputs['Metallic'].default_value=0; p.inputs['Roughness'].default_value=.53; p.inputs['Coat Weight'].default_value=.09
    coord=node(t,'ShaderNodeTexCoord','local',-900,0); sep=node(t,'ShaderNodeSeparateXYZ','thickness_axis',-650,0); t.links.new(coord.outputs['Object'],sep.inputs[0])
    phase=math_node(t,'MULTIPLY',sep.outputs[axis],2*3.14159265/.0062,-400,0)
    sine=node(t,'ShaderNodeMath','laminations',-200,0); sine.operation='SINE'; t.links.new(phase,sine.inputs[0])
    ramp=node(t,'ShaderNodeValToRGB','edge_tone',30,0)
    ramp.color_ramp.elements[0].position=.1; ramp.color_ramp.elements[0].color=color((.40,.24,.095))
    ramp.color_ramp.elements[1].position=.75; ramp.color_ramp.elements[1].color=color((.59,.38,.17))
    t.links.new(sine.outputs[0],ramp.inputs[0]); t.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    frame(t,'侧边：独立层压截面，局部厚度轴变化',[coord,sep,sine,ramp]); return m


def mesh_digest(ob):
    """输入对象，返回顶点、三角面、导入UV和自定义法线的保护哈希。"""
    data={'vertices':[list(v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons],
        'normals':[list(n.vector) for n in ob.data.corner_normals],
        'uv':{uv.name:[list(item.uv) for item in uv.data] for uv in ob.data.uv_layers if uv.name!='UV_WoodReference'}}
    return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()


def assign(ob,board):
    """输入木板和类型，新增投影UV／表面标记并替换材质；几何保持原样。"""
    across=2 if board=='seat' else 1; thickness=1 if board=='seat' else 2
    bounds=[(min(v.co[k] for v in ob.data.vertices),max(v.co[k] for v in ob.data.vertices)) for k in range(3)]
    ob.data=ob.data.copy(); uv=ob.data.uv_layers.new(name='UV_WoodReference')
    for loop in ob.data.loops:
        co=ob.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((co.x-bounds[0][0])/(bounds[0][1]-bounds[0][0]),(co[across]-bounds[across][0])/(bounds[across][1]-bounds[across][0]))
    ob.data.uv_layers.active=ob.data.uv_layers['UV_Material']; ob.data.uv_layers['UV_Material'].active_render=True
    attr=ob.data.attributes.new('reference_rear','FLOAT','FACE')
    mat,control=face_material(board); edge=edge_material('Y' if board=='seat' else 'Z')
    ob.data.materials.clear(); ob.data.materials.append(mat); ob.data.materials.append(edge)
    for polygon in ob.data.polygons:
        polygon.material_index=0 if abs(polygon.normal[thickness])>.52 else 1
        attr.data[polygon.index].value=float(board=='back' and polygon.normal.z<-.52)
    return control


def studio():
    """创建固定三点布光和透视机位，返回主光和相机。"""
    sc=bpy.context.scene
    for ob in list(sc.objects):
        if ob.type in {'LIGHT','CAMERA'}: bpy.data.objects.remove(ob,do_unlink=True)
    world=bpy.data.worlds.new('World'); world.use_nodes=True; sc.world=world
    world.node_tree.nodes['Background'].inputs[0].default_value=(.14,.14,.14,1); world.node_tree.nodes['Background'].inputs[1].default_value=.16
    lights=[]
    for role,pos,power,size in [('key',(-.60,-.65,1.30),55,.85),('fill',(.75,-.2,.90),15,.8),('rim',(.15,.8,1.2),45,.65)]:
        d=bpy.data.lights.new('Area','AREA'); d.energy=power; d.shape='DISK'; d.size=size
        ob=bpy.data.objects.new('Area',d); sc.collection.objects.link(ob); ob.location=pos; ob['wood_reference_role']=role; aim(ob,(0,0,.4)); lights.append(ob)
    d=bpy.data.cameras.new('Camera'); d.type='PERSP'; ob=bpy.data.objects.new('Camera',d); sc.collection.objects.link(ob); sc.camera=ob; d.clip_start=.01
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015)); floor=bpy.context.object
    m=bpy.data.materials.new('Studio neutral'); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(.085,.085,.085,1); p.inputs['Roughness'].default_value=.75; floor.data.materials.append(m)
    sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for device in prefs.devices: device.use=device.type=='OPTIX'
    sc.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    sc.render.resolution_x=1400; sc.render.resolution_y=1400; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_depth='16'
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=-.60
    sc.unit_settings.system='METRIC'; return lights[0],ob


def render(name,location,target,lens=65):
    """输入评审名和透视机位，输出固定色彩管理的渲染文件。"""
    sc=bpy.context.scene; sc.camera.location=location; sc.camera.data.lens=lens; aim(sc.camera,target)
    sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True); return name+'.png'


def main():
    """保护输入，应用两块木板的材质并保存评审工程及哈希。"""
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest(); bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    boards={'LP_part_02':'seat','LP_part_09':'back'}; before={name:mesh_digest(bpy.data.objects[name]) for name in boards}
    controls=[assign(bpy.data.objects[name],board) for name,board in boards.items()]
    after={name:mesh_digest(bpy.data.objects[name]) for name in boards}; assert before==after
    key,cam=studio(); renders=[]
    # 同灯、同机位保留原Tripo外观，随后恢复本轮材质。
    old=bpy.data.materials['Baked Wood PBR']; slots={name:list(bpy.data.objects[name].data.materials) for name in boards}
    for name in boards:
        for k in range(len(bpy.data.objects[name].data.materials)): bpy.data.objects[name].data.materials[k]=old
    renders.append(render('00_previous_tripo',(1.0,-1.3,.98),(0,0,.40),52))
    for name,materials in slots.items():
        for k,m in enumerate(materials): bpy.data.objects[name].data.materials[k]=m
    for c in controls:
        for name in PARAMS: c.inputs[name].default_value=0
    renders.append(render('01_process',(1.0,-1.3,.98),(0,0,.40),52))
    for c in controls:
        for name,value in PARAMS.items(): c.inputs[name].default_value=value
    renders.append(render('02_final',(1.0,-1.3,.98),(0,0,.40),52))
    renders.append(render('03_seat_detail',(.29,-.47,.85),(0,-.035,.405),55))
    renders.append(render('04_back_detail',(.28,-.57,.81),(0,.18,.685),72))
    renders.append(render('05_rear_detail',(-.34,.66,.80),(0,.18,.66),65))
    original=key.location.copy(); key.location=(-.5,-.45,.51); aim(key,(0,-.03,.4))
    renders.append(render('06_raking',(.28,-.50,.57),(0,-.04,.405),65)); key.location=original; aim(key,(0,0,.4))
    # 条形光诊断只改变灯形与观察角，观察连续高光中的微细变化。
    key.location=(-.15,-.15,.92); key.data.shape='RECTANGLE'; key.data.size=.55; key.data.size_y=.12; aim(key,(0,-.04,.405))
    renders.append(render('09_highlight_close',(.25,-.45,.62),(0,-.055,.405),62))
    key.location=original; key.data.shape='DISK'; key.data.size=.85; aim(key,(0,0,.4))
    cam.location=(1.0,-1.3,.98); cam.data.lens=52; aim(cam,(0,0,.4))
    bpy.ops.object.select_all(action='DESELECT'); ob=bpy.data.objects['LP_part_02']; ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.context.preferences.filepaths.save_version=0; path=WORK/'tripo_wood_reference.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(path))
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash,'blend':str(path.relative_to(ROOT)),
        'board_geometry_before':before,'board_geometry_after':after,'geometry_uv_normals_preserved':before==after,'parameters':PARAMS,'renders':renders,'projection_uv':'UV_WoodReference','preserved_uv':'UV_Material','camera':'PERSP','lights':3,'samples':64,'resolution':[1400,1400],'visual_status':'reference comparison pending; not user-approved'}
    (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
