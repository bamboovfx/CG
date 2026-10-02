"""在独立Blender候选中验证木椅工艺层／表现层。

输入：当前镜头内AST_school_chair_HP集合、SD工艺贴图和三个效果蒙版。
输出：透视三点布光工程、分层对照、座面掠射光；不保存或修改输入镜头。
参数：0.6m木纹覆盖、划痕0.38、老化0.30、边缘磨损0.42。
"""
from pathlib import Path
import hashlib
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
TEX = ROOT/'02_assets/textures/generated/wood_layers'
WORK = ROOT/'07_pipeline/cache/wood_layers_20260930'
OUT = ROOT/'06_review/wood_layers_20260930'
PARAMS = {'Scratches':.38, 'Age':.30, 'Wear':.42}


def node(tree, kind, role, x=0, y=0):
    """输入节点类型和内部用途，返回保留默认名称／标题的新节点。"""
    n=tree.nodes.new(kind); n.location=(x,y); n['wood_layers_role']=role
    return n


def socket(group, name, kind, direction='INPUT', default=None):
    """输入组接口名称、类型、方向及默认值，返回新接口；仅新建候选组。"""
    s=group.interface.new_socket(name=name,in_out=direction,socket_type=kind)
    if default is not None: s.default_value=default
    if kind=='NodeSocketFloat' and direction=='INPUT': s.min_value=0; s.max_value=1
    return s


def frame(tree, text, children):
    """输入说明文字与节点列表，创建独立注释框；不改节点可见标题。"""
    f=node(tree,'NodeFrame','comment'); f.label=text; f.use_custom_color=True; f.color=(.16,.21,.25)
    for child in children:
        xy=child.location.copy(); child.parent=f; child.location=xy
    return f


def image_node(tree, name, vector, x=0, y=0):
    """输入SD输出名和坐标接口，返回正确颜色空间的Image Texture节点。"""
    n=node(tree,'ShaderNodeTexImage',name,x,y)
    n.image=bpy.data.images.load(str(TEX/(name+'.png')),check_existing=True)
    n.image.colorspace_settings.name='sRGB' if 'BaseColor' in name else 'Non-Color'
    tree.links.new(vector,n.inputs['Vector']); n.interpolation='Linear'
    return n


def math_node(tree, op, a, b, x=0, y=0):
    """输入运算和常数／接口，返回浮点输出；用于蒙版与通道强度。"""
    n=node(tree,'ShaderNodeMath',op,x,y); n.operation=op
    for value, target in ((a,n.inputs[0]),(b,n.inputs[1])):
        if isinstance(value,(int,float)): target.default_value=value
        else: tree.links.new(value,target)
    return n.outputs[0]


def mix(tree, base, foreground, amount, role, x=0, y=0):
    """输入基础值、目标颜色／标量及蒙版，返回线性混合结果。"""
    n=node(tree,'ShaderNodeMixRGB',role,x,y); n.blend_type='MIX'
    tree.links.new(amount,n.inputs[0]); tree.links.new(base,n.inputs[1])
    if isinstance(foreground,(float,int)): n.inputs[2].default_value=(foreground,foreground,foreground,1)
    elif isinstance(foreground,tuple): n.inputs[2].default_value=foreground
    else: tree.links.new(foreground,n.inputs[2])
    return n.outputs[0]


def process_group():
    """返回工艺层组：米制木纹坐标读取SD五通道与高度，输出真实着色法线。"""
    g=bpy.data.node_groups.new('Wood / 工艺层 / 木纹着色与涂层','ShaderNodeTree')
    socket(g,'Vector','NodeSocketVector')
    for name, kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Metallic','NodeSocketFloat'),('Normal','NodeSocketVector'),('AO','NodeSocketFloat'),('Height','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-900,100); o=node(g,'NodeGroupOutput','output',400,100)
    textures=[]
    for k,(channel,output) in enumerate([('BaseColor','Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal'),('AO','AO'),('Height','Height')]):
        name='Height' if channel=='Height' else 'Process_'+channel
        t=image_node(g,name,i.outputs['Vector'],-560,450-k*210); textures.append(t)
        if channel=='Normal':
            n=node(g,'ShaderNodeNormalMap','OpenGL',0,-210); n.uv_map='WoodGrainMeters'; n.space='TANGENT'
            if hasattr(n,'convention'): n.convention='OPENGL'
            g.links.new(t.outputs['Color'],n.inputs['Color']); g.links.new(n.outputs['Normal'],o.inputs[output])
        else: g.links.new(t.outputs['Color'],o.inputs[output])
    frame(g,'工艺层：木纹／着色／涂层微起伏；Metallic=0；AO独立保留',textures)
    return g


def appearance_group():
    """返回表现层组：各效果独立控制，多通道对应，磨损限定在资产边缘。"""
    g=bpy.data.node_groups.new('Wood / 表现层 / 划痕老化磨损','ShaderNodeTree')
    for name,kind in [('Vector','NodeSocketVector'),('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Height','NodeSocketFloat'),('Edge','NodeSocketFloat')]: socket(g,name,kind)
    for name,value in PARAMS.items(): socket(g,name,'NodeSocketFloat',default=value)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Coat','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-1400,0); o=node(g,'NodeGroupOutput','output',1900,0)
    masks={}
    for k,(channel,param) in enumerate([('ScratchMask','Scratches'),('AgeMask','Age'),('WearBreakup','Wear')]):
        t=image_node(g,channel,i.outputs['Vector'],-1100,600-k*350)
        mask=math_node(g,'MULTIPLY',t.outputs['Color'],i.outputs[param],-800,600-k*350)
        if param=='Wear': mask=math_node(g,'MULTIPLY',mask,i.outputs['Edge'],-580,-100)
        masks[param]=mask
    age_color=mix(g,i.outputs['Color'],(.22,.12,.055,1),math_node(g,'MULTIPLY',masks['Age'],.28,-500,600),'age_color',-200,650)
    color=mix(g,age_color,(.35,.20,.085,1),masks['Wear'],'exposed_wood',140,650)
    color=mix(g,color,(.44,.28,.13,1),math_node(g,'MULTIPLY',masks['Scratches'],.10,-200,950),'scratch_color',460,650)
    long_mask=image_node(g,'LongScratchMask',i.outputs['Vector'],-1100,970)
    long_amount=math_node(g,'MULTIPLY',long_mask.outputs['Color'],i.outputs['Scratches'],-760,1050)
    color=mix(g,color,(.12,.05,.015,1),math_node(g,'MULTIPLY',long_amount,.6,-350,1140),'long_scratch_color',830,650)
    rough=mix(g,i.outputs['Roughness'],.54,masks['Age'],'age_rough',-200,280)
    rough=mix(g,rough,.64,masks['Wear'],'wear_rough',140,280)
    rough=mix(g,rough,.58,masks['Scratches'],'scratch_rough',460,280)
    # 已生成的工艺法线接入Bump基础法线，避免错误RGB相加。
    bump=node(g,'ShaderNodeBump','shallow_scratch',600,-120); bump.inputs['Distance'].default_value=.000075
    g.links.new(math_node(g,'SUBTRACT',0,masks['Scratches'],120,-170),bump.inputs['Height'])
    g.links.new(i.outputs['Normal'],bump.inputs['Normal'])
    fibre=math_node(g,'MULTIPLY',i.outputs['Height'],masks['Wear'],700,-460)
    bump2=node(g,'ShaderNodeBump','worn_fibre',1040,-120); bump2.inputs['Distance'].default_value=.000045
    g.links.new(fibre,bump2.inputs['Height']); g.links.new(bump.outputs['Normal'],bump2.inputs['Normal'])
    coat=math_node(g,'MULTIPLY',.12,math_node(g,'SUBTRACT',1,masks['Wear'],1000,500),1340,500)
    for output,value in [('Color',color),('Roughness',rough),('Normal',bump2.outputs['Normal']),('Coat',coat)]: g.links.new(value,o.inputs[output])
    frame(g,'表现层：划痕／老化／边缘磨损；各通道共享位置，响应分别控制',[n for n in g.nodes if n.type not in {'GROUP_INPUT','GROUP_OUTPUT','FRAME'}])
    return g


def material(pg, ag, object_name):
    """输入两层组和木板名称，返回具有真实边缘约束的独立候选材质。"""
    mat=bpy.data.materials.new('Wood layers / '+object_name); mat.use_nodes=True
    tree=mat.node_tree; p=tree.nodes.get('Principled BSDF'); out=tree.nodes.get('Material Output')
    p.location=(1100,180); out.location=(1450,180)
    uv=node(tree,'ShaderNodeUVMap','grain_meters',-1500,500); uv.uv_map='WoodGrainMeters'
    scale=node(tree,'ShaderNodeVectorMath','tile_0.6m',-1220,500); scale.operation='SCALE'; scale.inputs['Scale'].default_value=1/.6
    tree.links.new(uv.outputs['UV'],scale.inputs[0])
    proc=node(tree,'ShaderNodeGroup','process',-720,500); proc.node_tree=pg
    app=node(tree,'ShaderNodeGroup','appearance',260,400); app.node_tree=ag
    tree.links.new(scale.outputs['Vector'],proc.inputs['Vector']); tree.links.new(scale.outputs['Vector'],app.inputs['Vector'])
    for name in ('Color','Roughness','Normal','Height'): tree.links.new(proc.outputs[name],app.inputs[name])
    # 实测米制UV与跨面属性计算离边距离，破碎蒙版只在接触边缘露木。
    suv=node(tree,'ShaderNodeUVMap','surface_meters',-1500,-150); suv.uv_map='SurfaceMeters'
    sep=node(tree,'ShaderNodeSeparateXYZ','surface_xy',-1260,-150); tree.links.new(suv.outputs['UV'],sep.inputs[0])
    distances=[]
    for k,(axis,attribute) in enumerate([('X','surface_span_u'),('Y','surface_span_v')]):
        a=node(tree,'ShaderNodeAttribute','span',-1490,-430-k*230); a.attribute_name=attribute
        other=math_node(tree,'SUBTRACT',a.outputs['Fac'],sep.outputs[axis],-990,-300-k*220)
        distances.append(math_node(tree,'MINIMUM',sep.outputs[axis],other,-740,-300-k*220))
    distance=math_node(tree,'MINIMUM',distances[0],distances[1],-480,-300)
    remap=node(tree,'ShaderNodeMapRange','edge_18mm',-220,-300); remap.clamp=True
    remap.inputs['From Min'].default_value=.001; remap.inputs['From Max'].default_value=.018
    remap.inputs['To Min'].default_value=1; remap.inputs['To Max'].default_value=0
    tree.links.new(distance,remap.inputs['Value']); tree.links.new(remap.outputs['Result'],app.inputs['Edge'])
    for output,target in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Coat','Coat Weight')]: tree.links.new(app.outputs[output],p.inputs[target])
    tree.links.new(proc.outputs['Metallic'],p.inputs['Metallic'])
    p.inputs['Coat Roughness'].default_value=.25
    frame(tree,'工艺层：SD木纹五通道；0.6m覆盖；法线使用木纹UV',[uv,scale,proc])
    frame(tree,'表现层：三个独立强度；边缘磨损以米制UV限制',[app])
    frame(tree,'资产蒙版：18mm边缘区域，保持曲面与木纹位置一致',[n for n in tree.nodes if n.get('wood_layers_role') in {'surface_meters','surface_xy','span','SUBTRACT','MINIMUM','edge_18mm'}])
    mat['tile_metres']=.6; mat['ao_usage']='Stored, not multiplied into Base Color'; mat.asset_mark()
    return mat, app


def aim(ob, target):
    """输入相机／灯和世界目标点，使其负Z轴朝向目标；返回无。"""
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


def area(location, energy, size, target, role, color=(1,1,1)):
    """输入位置、瓦数、尺寸和目标，返回保留默认名称的面积灯。"""
    bpy.ops.object.light_add(type='AREA',location=location); ob=bpy.context.object
    ob.data.energy=energy; ob.data.shape='DISK'; ob.data.size=size; ob.data.color=color
    ob['wood_layers_role']=role; aim(ob,target); return ob


def render(name, location, target, lens=50):
    """输入输出名和透视机位，固定曝光／灯光渲染并返回文件路径。"""
    sc=bpy.context.scene; sc.camera.location=location; sc.camera.data.lens=lens; aim(sc.camera,target)
    path=OUT/(name+'.png'); sc.render.filepath=str(path)
    bpy.ops.render.render(write_still=True); print('RENDERED',name,flush=True)
    return str(path.relative_to(ROOT))


def main():
    """从磁盘只读载入现有木椅，创建独立工作室，渲染分层版本并保存验证清单。"""
    WORK.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(SOURCE),link=False) as (available, loaded):
        assert 'AST_school_chair_HP' in available.collections
        loaded.collections=['AST_school_chair_HP']
    chair=loaded.collections[0]; bpy.context.scene.collection.children.link(chair)
    bpy.context.view_layer.update()
    # 既有参考切割／边缘辅助集合保持不渲染；不修改真实椅子几何。
    for ob in chair.all_objects:
        if ob is None: continue
        if any(c.name=='chair_hp_edge_references' for c in ob.users_collection): ob.hide_render=True
        elif ob.type=='MESH': ob.hide_render=False
    pg,ag=process_group(),appearance_group(); controls=[]
    for ob in bpy.data.collections['chair_hp_wood'].objects:
        mat,control=material(pg,ag,ob.name); ob.data=ob.data.copy(); ob.data.materials[0]=mat; controls.append(control)
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.cycles.use_denoising=True
    preferences=bpy.context.preferences.addons['cycles'].preferences
    try:
        preferences.compute_device_type='OPTIX'; preferences.get_devices()
        devices=[d for d in preferences.devices if d.type=='OPTIX']
        for d in preferences.devices: d.use=d.type=='OPTIX'
        sc.cycles.device='GPU' if devices else 'CPU'
    except Exception: sc.cycles.device='CPU'
    sc.render.resolution_x=1200; sc.render.resolution_y=1200; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_depth='16'
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=0
    sc.unit_settings.system='METRIC'
    world=bpy.data.worlds.new('World'); world.use_nodes=True; sc.world=world
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.14,.18,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.16
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015)); floor=bpy.context.object
    fm=bpy.data.materials.new('Studio neutral'); fm.use_nodes=True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.085,.10,1)
    fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72; floor.data.materials.append(fm)
    target=(0,0,.4)
    key=area((-.7,.8,1.35),70,.85,target,'key',(1,.96,.90))
    area((.9,.2,.85),18,.75,target,'fill',(.88,.94,1))
    area((.2,-.85,1.2),55,.6,target,'rim',(1,1,1))
    bpy.ops.object.camera_add(location=(1.0,1.35,.95)); cam=bpy.context.object; sc.camera=cam; cam.data.type='PERSP'; cam.data.clip_start=.01
    cam.data.lens=52; aim(cam,target)
    stages=[('01_process',{}),('02_scratches',{'Scratches':PARAMS['Scratches']}),('03_age',{'Scratches':PARAMS['Scratches'],'Age':PARAMS['Age']}),('04_appearance',PARAMS)]
    renders=[]
    for name,params in stages:
        for ctrl in controls:
            for param in PARAMS: ctrl.inputs[param].default_value=params.get(param,0)
        renders.append(render(name,(1.0,1.35,.95),target,52))
    renders.append(render('05_seat_detail',(.42,.59,.79),(0,.045,.40),70))
    # 临时掠射机位与主光用于诊断，完成后恢复三点布光保存候选。
    key_loc=key.location.copy(); key.location=(-.5,.5,.57); aim(key,(0,.02,.4))
    renders.append(render('06_raking_detail',(.34,.56,.56),(0,.025,.4),70)); key.location=key_loc; aim(key,target)
    cam.location=(1.0,1.35,.95); cam.data.lens=52; aim(cam,target)
    for area_ui in bpy.context.screen.areas if bpy.context.screen else []:
        if area_ui.type=='VIEW_3D': area_ui.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.object.select_all(action='DESELECT')
    ob=bpy.data.objects['chair_dished_plywood_seat']; ob.select_set(True); bpy.context.view_layer.objects.active=ob
    # 以节点网络和相对路径保留编辑入口，不将灯光烘进基础色。
    dest=WORK/'wood_layers_studio.blend'; bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    audit={'input':str(SOURCE.relative_to(ROOT)),'input_sha256':source_hash,'input_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash,'blend':str(dest.relative_to(ROOT)),'parameters':PARAMS,'render_engine':sc.render.engine,'camera_type':cam.data.type,'resolution':[1200,1200],'samples':64,'wood_objects':[o.name for o in bpy.data.collections['chair_hp_wood'].objects],'node_groups':[pg.name,ag.name],'normal_uv':'WoodGrainMeters','tile_metres':.6,'edge_band_metres':.018,'renders':renders,'missing_images':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]}
    (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
