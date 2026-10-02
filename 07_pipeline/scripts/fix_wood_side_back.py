"""修复木椅侧立面的单轴条带和背面遗留合成印记，保留最新正面外观。

输入：用户最新保存候选；输出：独立修复工程和同光逐项隔离／前后渲染。
原顶点、面、原UV、自定义法线及五金保持；新增米制周长×厚度侧壁UV。
"""
from pathlib import Path
import sys
import json
import hashlib
import math
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import node,frame,math_node,mix,aim
from tripo_wood_reference_blender import color,mesh_digest
from tripo_wood_appearance_blender import process_signature

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930/tripo_wood_dirt.blend'
WORK=ROOT/'07_pipeline/cache/tripo_wood_side_back_20260930'
OUT=ROOT/'06_review/tripo_wood_side_back_20260930'
BOARDS=[('LP_part_02','seat',2,1),('LP_part_09','back',1,2)]


def hull(points):
    """输入二维板材投影点，返回逆时针外轮廓；不改网格或缝线。"""
    points=sorted(set(tuple(map(float,p)) for p in points))
    def cross(o,a,b):
        """输入三点，返回转向叉积，供凸轮廓构造。"""
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]; upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0: lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0: upper.pop()
        upper.append(p)
    return np.asarray(lower[:-1]+upper[:-1],dtype=np.float64)


def geometry_protection(ob):
    """输入木板，返回包含全部已有UV的保护摘要；新增侧壁UV另行验证。"""
    data={'vertices':[list(v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons],
        'normals':[list(n.vector) for n in ob.data.corner_normals],
        'uv':{u.name:[list(x.uv) for x in u.data] for u in ob.data.uv_layers if u.name!='UV_WoodEdge'}}
    return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()


def side_uv(ob,across,thickness):
    """输入木板、板宽轴和厚度轴，返回独立米制侧壁UV与真实面积畸变统计。"""
    mesh=ob.data; mesh.calc_loop_triangles(); contour=hull([[v.co.x,v.co[across]] for v in mesh.vertices])
    ends=np.roll(contour,-1,axis=0); delta=ends-contour; length=np.linalg.norm(delta,axis=1)
    cumulative=np.concatenate([[0],np.cumsum(length)])
    layer=mesh.uv_layers.new(name='UV_WoodEdge'); layer.active_render=False
    # 原有正面／烘焙UV继续作为原接口，不替换其坐标或切线基。
    mesh.uv_layers.active=mesh.uv_layers['UV_Material']; mesh.uv_layers['UV_Material'].active_render=True
    fallbacks=0; ratios=[]; side_count=0
    for poly in mesh.polygons:
        if poly.material_index!=1: continue
        loops=list(poly.loop_indices); coords=np.array([mesh.vertices[mesh.loops[l].vertex_index].co[:] for l in loops])
        plane=coords[:,[0,across]]; centre=plane.mean(axis=0)
        t=np.clip(np.einsum('ij,ij->i',centre-contour,delta)/(length*length),0,1)
        segment=int(np.argmin(np.linalg.norm(centre-(contour+t[:,None]*delta),axis=1)))
        tangent=delta[segment]/length[segment]
        u=cumulative[segment]+(plane-contour[segment])@tangent
        values=np.stack([u,coords[:,thickness]],axis=1)
        # 少量不沿外轮廓的小内壁使用局部米制平面，避免再次产生退化三角形。
        if len(loops)==3:
            area3=np.linalg.norm(np.cross(coords[1]-coords[0],coords[2]-coords[0]))
            area2=abs(np.linalg.det(np.stack([values[1]-values[0],values[2]-values[0]])))
            if area3>1e-12 and area2/area3<.25:
                edge=coords[1]-coords[0]; x=edge/np.linalg.norm(edge)
                normal=np.cross(edge,coords[2]-coords[0]); normal/=np.linalg.norm(normal); y=np.cross(normal,x)
                values=np.stack([(coords-coords[0])@x,(coords-coords[0])@y],axis=1)
                values+=np.array([u.mean(),coords[:,thickness].mean()]); fallbacks+=1
        for loop,value in zip(loops,values): layer.data[loop].uv=value
    for tri in mesh.loop_triangles:
        if mesh.polygons[tri.polygon_index].material_index!=1: continue
        co=np.array([mesh.vertices[i].co[:] for i in tri.vertices]); a=np.array([layer.data[l].uv[:] for l in tri.loops])
        area3=np.linalg.norm(np.cross(co[1]-co[0],co[2]-co[0]))
        area2=abs(np.linalg.det(np.stack([a[1]-a[0],a[2]-a[0]])))
        if area3>1e-12: ratios.append(float(area2/area3))
        side_count+=1
    assert ratios and min(ratios)>.20,(ob.name,min(ratios))
    return {'perimeter_m':float(cumulative[-1]),'side_triangles':side_count,'local_fallback_faces':fallbacks,
        'uv_area_over_3d_area_min':min(ratios),'uv_area_over_3d_area_max':max(ratios),'degenerate_triangles':sum(v<1e-5 for v in ratios)}


def noise(tree,vector,scale,role,detail=3):
    """输入米制UV、各轴频率和用途，返回确定性的侧截面多尺度噪声。"""
    mapping=node(tree,'ShaderNodeVectorMath',role+'_scale'); mapping.operation='MULTIPLY'
    tree.links.new(vector,mapping.inputs[0]); mapping.inputs[1].default_value=scale
    n=node(tree,'ShaderNodeTexNoise',role); n.noise_dimensions='3D'; n.inputs['Scale'].default_value=1
    n.inputs['Detail'].default_value=detail; n.inputs['Roughness'].default_value=.68
    tree.links.new(mapping.outputs['Vector'],n.inputs['Vector']); return n.outputs['Fac']


def edge_material(old,board):
    """输入旧侧边材质及板名，返回物理侧壁UV驱动的自然截面材质；旧文件不修改。"""
    mat=old.copy(); mat.name='Wood / side cross-section / '+board; t=mat.node_tree; t.nodes.clear()
    uv=node(t,'ShaderNodeUVMap','edge_uv',-1000,250); uv.uv_map='UV_WoodEdge'
    strata=noise(t,uv.outputs['UV'],(24,1650,1),'irregular_cut_strata')
    micro=noise(t,uv.outputs['UV'],(410,5800,1),'cut_fibre_microdetail',2)
    broad=noise(t,uv.outputs['UV'],(7,145,1),'cut_colour_clouds',2)
    signal=math_node(t,'ADD',math_node(t,'MULTIPLY',strata,.68),math_node(t,'MULTIPLY',micro,.32))
    ramp=node(t,'ShaderNodeValToRGB','natural_cut_colour',0,380)
    ramp.color_ramp.elements[0].position=.20; ramp.color_ramp.elements[0].color=color((.29,.165,.063))
    ramp.color_ramp.elements[1].position=.79; ramp.color_ramp.elements[1].color=color((.63,.427,.206))
    mid=ramp.color_ramp.elements.new(.51); mid.color=color((.48,.295,.12))
    t.links.new(signal,ramp.inputs['Fac'])
    colour=mix(t,ramp.outputs['Color'],color((.29,.175,.077)),math_node(t,'MULTIPLY',broad,.16),'local_cut_discolouration',350,380)
    rough=math_node(t,'ADD',.44,math_node(t,'MULTIPLY',micro,.20),350,70)
    bump=node(t,'ShaderNodeBump','cut_microrelief',350,-230); bump.inputs['Distance'].default_value=.000022
    bump.inputs['Strength'].default_value=.55; t.links.new(micro,bump.inputs['Height'])
    shader=node(t,'ShaderNodeBsdfPrincipled','cut_surface',720,200); shader.inputs['Metallic'].default_value=0
    shader.inputs['Coat Weight'].default_value=.055; shader.inputs['Coat Roughness'].default_value=.43
    for source,target in [(colour,'Base Color'),(rough,'Roughness'),(bump.outputs['Normal'],'Normal'),(bump.outputs['Normal'],'Coat Normal')]: t.links.new(source,shader.inputs[target])
    out=node(t,'ShaderNodeOutputMaterial','output',1100,200); t.links.new(shader.outputs['BSDF'],out.inputs['Surface'])
    # 拓扑依赖排版，说明独立于软件默认节点名称。
    depths={}; rows={}
    for _ in range(len(t.nodes)):
        for n in t.nodes:
            parents=[l.from_node.name for l in t.links if l.to_node==n]
            if all(p in depths for p in parents): depths[n.name]=max([depths[p] for p in parents] or [0])+1
    for n in t.nodes:
        d=depths.get(n.name,0); row=rows.get(d,0); rows[d]=row+1; n.location=(d*250,-row*250)
    frame(t,'侧立面：米制周长×厚度UV；不规则薄层与切口纤维，移除贯穿一圈的等宽正弦条带',[n for n in t.nodes if n!=out])
    mat['wood_side_uv']='UV_WoodEdge'; return mat


def disable_stamp(app):
    """输入实际表现组，断开遗留合成印记的颜色Factor；其余旧化路径保持。"""
    g=app.node_tree; mix=next(n for n in g.nodes if n.get('wood_layers_role')=='rear_stamp_preserved')
    for link in list(g.links):
        if link.to_socket==mix.inputs[0]: g.links.remove(link)
    mix.inputs[0].default_value=0
    # 保留旧资源作为可追溯资料，颜色输出不再包含这块人工周期矩形。
    g['legacy_stamp_disabled']=True
    f=node(g,'NodeFrame','stamp_note'); f.label='遗留合成矩形印记已关闭；不是UV／法线异常，不作为真实污渍'


def render(name,view,width=1600,height=1000):
    """输入同视角机位，输出实际材质前后图，固定光照与随机种子。"""
    sc=bpy.context.scene; sc.camera.location=view[0]; sc.camera.data.lens=view[2]; aim(sc.camera,view[1])
    sc.render.resolution_x=width; sc.render.resolution_y=height; sc.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True); print('SIDE_BACK_RENDER '+name,flush=True)


def main():
    """复现两种异常、一次只改对应分支，保存独立候选和保护／侧UV证据。"""
    for folder in (WORK,OUT): folder.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest(); bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    sc=bpy.context.scene; camera=(sc.camera.location.copy(),sc.camera.rotation_euler.copy(),sc.camera.data.lens)
    renderstate=(sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath,sc.cycles.samples)
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    sc.cycles.device='GPU'; sc.cycles.samples=96; sc.cycles.seed=930; sc.render.image_settings.color_depth='16'
    protected={}; process={}; dirt={}; controls={}; apps={}
    for obj,board,across,thickness in BOARDS:
        ob=bpy.data.objects[obj]; t=ob.data.materials[0].node_tree
        protected[board]=geometry_protection(ob)
        p=next(n for n in t.nodes if n.get('wood_layers_role')=='process'); process[board]=process_signature(p.node_tree)
        d=next(n for n in t.nodes if n.get('wood_layers_role')=='surface_dirt'); dirt[board]=process_signature(d.node_tree)
        app=next(n for n in t.nodes if n.get('wood_layers_role')=='appearance'); apps[board]=app
        controls[board]={k:app.inputs[k].default_value for k in ['Age','Wear','Scratches']}
    side=((0,-.98,.423),(0,-.015,.400),70)
    rear=((0,.95,.73),(0,.168,.673),65)
    corner=((.39,-.57,.49),(0,-.07,.40),72)
    top=((.29,-.47,.85),(0,-.035,.405),55)
    render('00_side_before',side); render('01_back_before',rear)
    render('02_corner_before',corner); render('03_top_before',top,1400,1400)
    for app in apps.values(): disable_stamp(app)
    render('04_back_stamp_off',rear)
    uvstats={}
    for obj,board,across,thickness in BOARDS:
        ob=bpy.data.objects[obj]; uvstats[board]=side_uv(ob,across,thickness)
        ob.data.materials[1]=edge_material(ob.data.materials[1],board)
    render('05_side_after',side); render('06_back_after',rear); render('07_corner_after',corner)
    render('08_top_after',top,1400,1400)
    assert all(geometry_protection(bpy.data.objects[obj])==protected[board] for obj,board,_,_ in BOARDS)
    for obj,board,_,_ in BOARDS:
        t=bpy.data.objects[obj].data.materials[0].node_tree
        assert process_signature(next(n.node_tree for n in t.nodes if n.get('wood_layers_role')=='process'))==process[board]
        assert process_signature(next(n.node_tree for n in t.nodes if n.get('wood_layers_role')=='surface_dirt'))==dirt[board]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
    sc.camera.location,sc.camera.rotation_euler,sc.camera.data.lens=camera
    sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath,sc.cycles.samples=renderstate
    bpy.context.preferences.filepaths.save_version=0; path=WORK/'tripo_wood_side_back.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'blend':str(path.relative_to(ROOT)),
        'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometry_original_uv_normals':protected,
        'process':process,'dirt':dirt,'appearance_controls':controls,'side_uv':uvstats,'samples':96,
        'causes':['Legacy synthetic rectangular StampMask branch in base colour','Side shader read only thickness coordinate sine; face-projection UV is degenerate on side walls'],
        'source_unchanged':True,'visual_status':'Side and back repair pending user visual review'}
    (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SIDE_BACK_FIXED '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
