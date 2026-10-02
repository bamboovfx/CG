"""用 Blender Cloth 求解四片束拢窗帘；保存可重算工程、烘焙缓存和稳定网格。

输入：当前建筑源中的布料材质、挂钩和束带位置。输出：候选模拟工程和逐片求解网格。
顶部挂点及束带一圈由形态键收拢，其他点由重力、弯曲和自碰撞求解。
"""
import bpy
import json
import math
import time
from pathlib import Path
from mathutils import Vector

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/cloth_tone_20260918'
OUT=ROOT/'06_review/cloth_tone'
SIM=CACHE/'curtain_simulation.blend'
NU,NV=60,100
START,END=1,120
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=24
scene.frame_start=START
scene.frame_end=END
scene.gravity=(0,0,-9.81)
bpy.context.preferences.filepaths.save_version=0
with bpy.data.libraries.load(str(ROOT/'02_assets/work/classroom_environment.blend'),link=False) as (src,dst):
    dst.collections=[f'AST_gathered_curtain_{i:02d}' for i in range(4)]
for col in dst.collections:scene.collection.children.link(col)
bpy.ops.file.make_paths_absolute()


def make_collider(name,vertices,faces):
    """输入名字和网格，返回只参与碰撞的墙面对象；渲染隐藏。"""
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    obj=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(obj)
    obj.modifiers.new('Collision','COLLISION')
    obj.collision.thickness_outer=.004
    obj.collision.thickness_inner=.004
    obj.hide_render=True
    obj.display_type='WIRE'
    return obj


make_collider('SIM window plane',[(-3.947,-6.3,.3),(-3.947,4.9,.3),(-3.947,4.9,3.5),(-3.947,-6.3,3.5)],[(0,1,2,3)])
reports=[]
sim_objects=[]
for idx,col in enumerate(dst.collections):
    old=next(o for o in col.objects if o.get('continuous_surface'))
    original_matrix=old.matrix_world.copy()
    source_name=old.name
    original_top=[original_matrix@old.data.vertices[180*101+i*10].co for i in range(11)]
    top_center=sum(p.y for p in original_top)/11
    y0=[-5.5946,-2.4946,.8054,4.2554][idx]
    seed=.23+idx*.73
    tie_z=1.53+.035*math.sin(seed)
    tie_row=round((tie_z-.946)/2.334*NV)
    material=old.data.materials[0]
    # 原手工布面只存在于本轮恢复文件，模拟工程中换成均匀连续网格。
    bpy.data.objects.remove(old,do_unlink=True)
    verts=[];faces=[];targets=[]
    for j in range(NV+1):
        v=j/NV
        for i in range(NU+1):
            u=i/NU
            x=-3.798+.006*math.sin(20*math.pi*u+seed*.1)
            y=y0+(u-.5)*1.02
            z=.946+2.334*v
            verts.append((x,y,z))
            targets.append((x,y,z))
    for j in range(NV):
        for i in range(NU):
            a=j*(NU+1)+i
            faces.append((a,a+1,a+NU+2,a+NU+1))
    mesh=bpy.data.meshes.new('Cloth continuous grid')
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(material)
    obj=bpy.data.objects.new(source_name,mesh)
    col.objects.link(obj)
    for polygon in mesh.polygons:polygon.use_smooth=True
    uv=mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        i=loop.vertex_index%(NU+1);j=loop.vertex_index//(NU+1)
        uv.data[loop.index].uv=(i/NU*1.02,j/NV*2.334)
    pin=obj.vertex_groups.new(name='Pin_Hooks_And_Tieback')
    for i in range(NU+1):
        u=i/NU
        # 挂钩沿用已经安装的真实位置；间隔三点保持柔软的挂头。
        top_index=NV*(NU+1)+i
        if i%6 in (0,1,5):
            interval=min(9,int(u*10));fraction=u*10-interval
            target=original_top[interval].lerp(original_top[interval+1],fraction)
            targets[top_index]=tuple(target)
            pin.add([top_index],1.0,'REPLACE')
        # 束带约束为窄折线环，驱动布料收拢，不固定整片布面。
        vi=tie_row*(NU+1)+i
        targets[vi]=(-3.799+.036*math.sin(12*math.pi*u+seed*.08),
                     y0-.155+(u-.5)*.250,tie_z)
        pin.add([vi],1.0,'REPLACE')
    obj.shape_key_add(name='Basis')
    key=obj.shape_key_add(name='Gather_To_Existing_Hooks_And_Tie')
    for vi,target in enumerate(targets):key.data[vi].co=target
    key.value=0;key.keyframe_insert('value',frame=START)
    key.value=1;key.keyframe_insert('value',frame=55)
    # Cloth 位于细分和厚度之前；参数单位与实际米制布面一致。
    cloth=obj.modifiers.new('Cloth','CLOTH')
    cs=cloth.settings
    cs.quality=8;cs.mass=.18;cs.air_damping=3
    cs.tension_stiffness=25;cs.compression_stiffness=25;cs.shear_stiffness=12
    cs.bending_stiffness=.08
    cs.tension_damping=8;cs.compression_damping=8;cs.shear_damping=6;cs.bending_damping=.5
    cs.vertex_group_mass=pin.name;cs.pin_stiffness=1
    collision=cloth.collision_settings
    collision.use_collision=True;collision.distance_min=.003;collision.collision_quality=4
    collision.use_self_collision=True;collision.self_distance_min=.0025;collision.self_friction=5
    cloth.point_cache.frame_start=START;cloth.point_cache.frame_end=END
    cloth.point_cache.name=f'curtain_{idx:02d}'
    cloth.point_cache.use_disk_cache=True
    obj['simulation_method']='Blender Cloth: gravity + animated hook/tie pinning + self collision'
    obj['simulation_frames']=[START,END]
    obj['original_transform']=[list(row) for row in original_matrix]
    obj['continuous_surface']=True
    sim_objects.append(obj)
    reports.append({'object':obj.name,'collection':col.name,'vertices':len(verts),'faces':len(faces),
                    'pin_vertices':len([v for v in mesh.vertices if v.groups]),
                    'tie_row':tie_row,'source_transform':[list(row) for row in original_matrix]})

# 保存后生成磁盘缓存；实际逐帧计算，不能仅设置修改器后标记“已模拟”。
scene.frame_set(START)
bpy.ops.wm.save_as_mainfile(filepath=str(SIM),compress=True)
started=time.time()
for frame in range(START,END+1):
    scene.frame_set(frame)
    deps=bpy.context.evaluated_depsgraph_get()
    for obj in sim_objects:
        evaluated=obj.evaluated_get(deps)
        evaluated.to_mesh();evaluated.to_mesh_clear()
    if frame%10==0:print(f'CLOTH_FRAME {frame} / {END} elapsed {time.time()-started:.1f}s',flush=True)

for obj,report in zip(sim_objects,reports):
    cloth=obj.modifiers['Cloth']
    with bpy.context.temp_override(point_cache=cloth.point_cache,object=obj,active_object=obj):
        bpy.ops.ptcache.bake_from_cache()
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    result_mesh=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
    coords=[list(v.co) for v in result_mesh.vertices]
    delta=[(Vector(c)-obj.data.vertices[i].co).length for i,c in enumerate(coords)]
    assert max(delta)>.08, '布面没有形成有效模拟位移'
    assert all(math.isfinite(c) for p in coords for c in p)
    report.update({'baked':cloth.point_cache.is_baked,'max_displacement_m':max(delta),
                   'mean_displacement_m':sum(delta)/len(delta),
                   'bbox':[[min(p[k] for p in coords),max(p[k] for p in coords)] for k in range(3)]})
    assert report['baked']
    (CACHE/(obj.name.replace(' ','_')+'_solved.json')).write_text(json.dumps({'vertices':coords,'report':report}),encoding='utf-8')
    bpy.data.meshes.remove(result_mesh)
    sub=obj.modifiers.new('Subdivision','SUBSURF');sub.levels=1;sub.render_levels=2
    solid=obj.modifiers.new('Solidify','SOLIDIFY');solid.thickness=.00045;solid.offset=0
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=str(SIM),compress=True)
(OUT/'simulation.json').write_text(json.dumps({'method':'Actual Blender Cloth solve','frames':[START,END],
    'elapsed_seconds':time.time()-started,'curtains':reports},ensure_ascii=False,indent=2),encoding='utf-8')
print('CLOTH_SIMULATION_OK',flush=True)
