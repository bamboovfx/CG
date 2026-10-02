"""胶脚分层材质候选：原生4K内容、局部坐标绑定、轻度老化与近地脏渍；保留其它编辑。"""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import chair_metal_blender as common
from chair_metal_blender import node, math, vector, blend, clamp, bump, arrange
from wood_layers_blender import socket, aim
from tripo_wood_reference_blender import color
from tripo_wood_appearance_blender import process_signature
from cleanup_wood_rear_stamp import geometry_digest

TEX=ROOT/'02_assets/textures/generated/chair_foot_caps'
WORK=ROOT/'07_pipeline/cache/chair_foot_cap_materials_20261001'
OUT=ROOT/'06_review/chair_foot_cap_materials_20261001'
CANDIDATE=WORK/'foot_cap_materials_candidate.blend'
PROCESS='Foot caps / 工艺层 / 浅黄哑光模塑胶质'
APPEARANCE='Foot caps / 表现层 / 老化擦伤与近地脏渍'
CONTROLS={'Age':.75,'Wear':.75,'Scratches':.70,'Dirt':.65}


def protected():
    """读取全部几何UV法线、非新胶脚材质组和场景变换，返回保护摘要。"""
    return {'geometry':{o.name:geometry_digest(o.data) for o in bpy.data.objects if o.type=='MESH'},
            'transforms':{o.name:[list(row) for row in o.matrix_world] for o in bpy.data.objects},
            'materials':{m.name:process_signature(m.node_tree) for m in bpy.data.materials
                         if m.node_tree and not m.get('foot_cap_layers')},
            'groups':{g.name:process_signature(g) for g in bpy.data.node_groups if not g.name.startswith('Foot caps /')}}


def content(tree,name,coords):
    """输入SD通道及米制归一化坐标，返回显式三向混合；恢复共享工具原贴图路径。"""
    old=common.TEX
    try:
        common.TEX=TEX
        return common.image(tree,name,coords)
    finally:
        common.TEX=old


def group(name):
    """输入自建组名称，返回包含默认Group Input／Output的空组及节点。"""
    assert name not in bpy.data.node_groups
    g=bpy.data.node_groups.new(name,'ShaderNodeTree')
    i=node(g,'NodeGroupInput','input')
    o=node(g,'NodeGroupOutput','output')
    return g,i,o


def process_group():
    """输出干净胶脚工艺：SD颜色／粗糙度、微米模塑Bump、Metallic=0和独立AO。"""
    g,i,o=group(PROCESS)
    socket(g,'Vector','NodeSocketVector')
    socket(g,'Tint','NodeSocketColor',default=(1,1,1,1))
    socket(g,'Roughness','NodeSocketFloat',default=.61)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),
                      ('Metallic','NodeSocketFloat'),('Normal','NodeSocketVector'),('AO','NodeSocketFloat')]:
        socket(g,name,kind,'OUTPUT')
    base=content(g,'Process_BaseColor',i.outputs['Vector'])
    tint=blend(g,base,i.outputs['Tint'],1,'factory_tint')
    tint.node.blend_type='MULTIPLY'
    r=content(g,'Process_Roughness',i.outputs['Vector'])
    r=clamp(g,math(g,'ADD',math(g,'SUBTRACT',r,.61),i.outputs['Roughness']))
    h=content(g,'Process_Height',i.outputs['Vector'])
    n=bump(g,h,None,.000020,'moulded_microrelief')
    for name,value in [('Color',tint),('Roughness',r),('Normal',n)]:
        g.links.new(value,o.inputs[name])
    o.inputs['Metallic'].default_value=0
    o.inputs['AO'].default_value=1
    arrange(g,'工艺层：浅黄模塑胶质，细微反射／20µm高度标尺；Metallic=0；AO独立')
    return g


def appearance_group():
    """输出表现层：原4K内容乘胶脚局部高度包络，四个强度归零恢复工艺通道。"""
    g,i,o=group(APPEARANCE)
    for name,kind in [('Vector','NodeSocketVector'),('Height Fraction','NodeSocketFloat'),
                      ('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),
                      ('Metallic','NodeSocketFloat'),('Normal','NodeSocketVector'),('AO','NodeSocketFloat')]:
        socket(g,name,kind)
    for k,v in CONTROLS.items():
        socket(g,k,'NodeSocketFloat',default=v)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),
                      ('Metallic','NodeSocketFloat'),('Normal','NodeSocketVector'),('AO','NodeSocketFloat')]:
        socket(g,name,kind,'OUTPUT')
    t={k:content(g,k,i.outputs['Vector']) for k in ['AgeMask','WearMask','ScratchMask','DirtMask','DirtColor','DirtHeight']}
    h=i.outputs['Height Fraction']
    bottom=clamp(g,math(g,'DIVIDE',math(g,'SUBTRACT',.70,h),.70))
    lower_edge=clamp(g,math(g,'DIVIDE',math(g,'SUBTRACT',.14,h),.14))
    upper_edge=clamp(g,math(g,'DIVIDE',math(g,'SUBTRACT',h,.88),.12))
    edge=math(g,'MAXIMUM',lower_edge,upper_edge)
    age=math(g,'MULTIPLY',t['AgeMask'],i.outputs['Age'])
    wear_field=math(g,'MULTIPLY',t['WearMask'],math(g,'ADD',math(g,'MULTIPLY',edge,.35),.65))
    wear=math(g,'MULTIPLY',wear_field,i.outputs['Wear'])
    scratch=math(g,'MULTIPLY',t['ScratchMask'],i.outputs['Scratches'])
    # 地面接触加不均匀内容，避免整圈同色黑带；顶部接缝仅极轻积灰。
    contact=math(g,'MULTIPLY',bottom,math(g,'ADD',math(g,'MULTIPLY',t['DirtMask'],.85),math(g,'MULTIPLY',t['AgeMask'],.15)))
    contact=math(g,'ADD',contact,math(g,'MULTIPLY',upper_edge,math(g,'MULTIPLY',t['DirtMask'],.25)))
    dirt=clamp(g,math(g,'MULTIPLY',contact,i.outputs['Dirt']))
    c=blend(g,i.outputs['Color'],color((.69,.60,.37)),math(g,'MULTIPLY',age,.75),'warm_polymer_age')
    c=blend(g,c,color((.84,.82,.72)),math(g,'MULTIPLY',wear,.80),'scuff_colour')
    c=blend(g,c,color((.46,.43,.33)),math(g,'MULTIPLY',scratch,.70),'scratch_colour')
    c=blend(g,c,t['DirtColor'],dirt,'contact_dirt_colour')
    r=blend(g,i.outputs['Roughness'],.70,age,'aged_reflection')
    r=blend(g,r,.82,wear,'scuff_reflection')
    r=blend(g,r,.76,scratch,'scratch_reflection')
    r=blend(g,r,.83,dirt,'dust_reflection')
    n=bump(g,math(g,'MULTIPLY',scratch,-1),i.outputs['Normal'],.000110,'shallow_scratch_relief')
    n=bump(g,math(g,'MULTIPLY',wear,-.35),n,.000080,'shallow_scuff_relief')
    n=bump(g,math(g,'MULTIPLY',math(g,'SUBTRACT',t['DirtHeight'],.5),dirt),n,.000025,'fine_dust_relief')
    for name,value in [('Color',c),('Roughness',r),('Normal',n),('Metallic',i.outputs['Metallic']),('AO',i.outputs['AO'])]:
        g.links.new(value,o.inputs[name])
    arrange(g,'表现层：温和黄化／浅擦伤／细划痕／底边脏渍；胶脚始终非金属，四个强度归零恢复工艺')
    return g


def create_material(ob,proc,app,index):
    """输入胶脚和共享两层组，输出该胶脚独立根材质；坐标锁在物体局部。"""
    mat=bpy.data.materials.new('Foot caps / Layers / '+ob.name)
    mat.use_nodes=True
    mat['foot_cap_layers']=True
    mat['foot_cap_bound_part']=ob.name
    tree=mat.node_tree
    shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['IOR'].default_value=1.46
    shader.inputs['Metallic'].default_value=0
    shader.inputs['Coat Weight'].default_value=0
    coord=node(tree,'ShaderNodeTexCoord','local_coordinate')
    rotation=node(tree,'ShaderNodeVectorRotate','original_rotation')
    rotation.rotation_type='EULER_XYZ'
    rotation.inputs['Rotation'].default_value=ob.matrix_world.to_euler()
    tree.links.new(coord.outputs['Object'],rotation.inputs['Vector'])
    position=vector(tree,'ADD',rotation.outputs[0],tuple(ob.matrix_world.translation))
    tile=vector(tree,'MULTIPLY',position,(12.5,12.5,12.5))
    sep=node(tree,'ShaderNodeSeparateXYZ','bound_height')
    tree.links.new(position,sep.inputs[0])
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    zmin=min(p.z for p in pts); zmax=max(p.z for p in pts)
    height=clamp(tree,math(tree,'DIVIDE',math(tree,'SUBTRACT',sep.outputs['Z'],zmin),zmax-zmin))
    p=node(tree,'ShaderNodeGroup','process');p.node_tree=proc;p['foot_cap_role']='process'
    a=node(tree,'ShaderNodeGroup','appearance');a.node_tree=app;a['foot_cap_role']='appearance'
    tree.links.new(tile,p.inputs['Vector']);tree.links.new(tile,a.inputs['Vector'])
    tree.links.new(height,a.inputs['Height Fraction'])
    for k in ['Color','Roughness','Metallic','Normal','AO']:
        tree.links.new(p.outputs[k],a.inputs[k])
    for k,v in CONTROLS.items():
        a.inputs[k].default_value=v
    a.inputs['Dirt'].default_value=[.65,.60,.70,.63][index]
    for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
        tree.links.new(a.outputs[source],shader.inputs[dest])
    arrange(tree,'胶脚：工艺与表现独立；Object坐标绑定原装配，8cm内容周期；高度包络锁在本胶脚')
    return mat


def build_materials():
    """输入当前四个已分件胶脚，输出材质槽记录并核对其它资产完全保留。"""
    before=protected()
    caps=list(bpy.data.collections['CHAIR / Foot caps'].objects)
    assert len(caps)==4
    proc=process_group(); app=appearance_group()
    records=[]
    for index,ob in enumerate(caps):
        mat=create_material(ob,proc,app,index)
        assert len(ob.data.materials)==1
        old=ob.active_material.name
        ob.data.materials[0]=mat
        records.append({'part':ob.name,'material':mat.name,'previous_material':old})
    bpy.context.view_layer.update()
    assert protected()==before,'几何、UV或其它材质发生变化'
    return {'parts':records,'protected_unchanged':True,'controls':CONTROLS,'tile_m':.08}


def render(file,view,width,height,samples=32):
    """输入透视机位、尺寸和采样，输出保持原三点灯光与色彩管理的实际评审图。"""
    sc=bpy.context.scene
    sc.camera.location=view[0];aim(sc.camera,view[1]);sc.camera.data.lens=view[2]
    sc.render.resolution_x=width;sc.render.resolution_y=height;sc.render.resolution_percentage=100
    sc.cycles.samples=samples
    sc.render.filepath=str(OUT/file)
    bpy.ops.render.render(write_still=True)


def candidate():
    """输入含用户编辑的备份，输出分层近景、真实归零／工艺对照与恢复机位后的候选。"""
    OUT.mkdir(parents=True,exist_ok=True)
    sc=bpy.context.scene;cam=sc.camera
    snapshot=(cam.location.copy(),cam.rotation_euler.copy(),cam.data.lens,
              sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
              sc.render.filepath,sc.cycles.samples,sc.cycles.seed,sc.cycles.device,sc.render.image_settings.color_depth,
              sc.cycles.use_animated_seed)
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for device in prefs.devices:
        device.use=device.type=='CUDA'
    sc.cycles.device='GPU';sc.cycles.seed=101;sc.cycles.use_animated_seed=False;sc.render.image_settings.color_depth='8'
    audit=build_materials()
    view=((.85,-1.12,.39),(0,-.025,.06),70)
    close=((.27,-.365,.079),(.194,-.213,-.001),90)
    render('feet.png',view,1280,804,32)
    render('front_cap.png',close,1000,900,64)
    saved=[]
    for record in audit['parts']:
        mat=bpy.data.materials[record['material']]
        app=next(n for n in mat.node_tree.nodes if n.get('foot_cap_role')=='appearance')
        values={k:app.inputs[k].default_value for k in CONTROLS}
        saved.append((mat,app,values))
        for k in CONTROLS:
            app.inputs[k].default_value=0
    render('zero.png',close,640,576,16)
    for mat,app,_ in saved:
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        proc=next(n for n in mat.node_tree.nodes if n.get('foot_cap_role')=='process')
        for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
            mat.node_tree.links.new(proc.outputs[source],shader.inputs[dest])
    render('process.png',close,640,576,16)
    for mat,app,values in saved:
        for k,v in values.items():
            app.inputs[k].default_value=v
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
            mat.node_tree.links.new(app.outputs[source],shader.inputs[dest])
    (cam.location,cam.rotation_euler,cam.data.lens,
     sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
     sc.render.filepath,sc.cycles.samples,sc.cycles.seed,sc.cycles.device,sc.render.image_settings.color_depth,
     sc.cycles.use_animated_seed)=snapshot
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    (OUT/'candidate.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FOOT_CAP_MATERIALS_CANDIDATE '+json.dumps(audit),flush=True)


if __name__=='__main__':
    candidate()
