"""按厂商零件图修正左侧外窗五金；输入当前建筑源，输出候选和几何验证。

尺寸依据：HHJ-0895 底座23.3×66 / 孔距40mm；HHK12630 拉手26×134 / 槽16×105mm。
锁的侧面安装依据 HHW11-050 与 E16191006。轨道适配尺寸属于本镜头制作设定。
仅修改 AST_window_wall_left 的当前六组五金；不执行旧场景生成脚本。
"""
import bpy
import bmesh
import math
import json
import sys
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
REVIEW = ROOT / '06_review/window_hardware_correction'
CACHE = ROOT / '07_pipeline/cache/window_hardware_correction_20260927'
REV = 'window_hardware_20260927'
REF_LOCK = 'https://parts.ykkap.co.jp/shop/g/gYKHHW-HHJ-0895/'
REF_PULL = 'https://parts.ykkap.co.jp/shop/g/gCHHHW-HHK12630/'


def center(obj):
    """输入对象，返回世界包围盒中心；支持历史模型的偏移原点。"""
    return sum((obj.matrix_world @ Vector(v) for v in obj.bound_box), Vector()) / 8


def rounded(w, h, r, count=6):
    """输入宽高与圆角半径，返回逆时针二维轮廓。"""
    pts=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(count+1):
            a=math.radians(start+j*90/count)
            pts.append((x+r*math.cos(a),y+r*math.sin(a)))
    return pts


def prism(poly, depth, axis='Y'):
    """输入平面轮廓/厚度/法线轴，返回实体网格顶点与面。"""
    def point(u,v,d):
        return (u,d,v) if axis=='Y' else (d,u,v)
    n=len(poly)
    vs=[point(u,v,d) for d in (-depth/2,depth/2) for u,v in poly]
    fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return vs,fs


def ring(outer, inner, depth, axis='Y'):
    """输入等点数内外轮廓及厚度，返回带真实贯通孔的封闭环形网格。"""
    assert len(outer)==len(inner)
    n=len(outer)
    def point(p,d):
        return (p[0],d,p[1]) if axis=='Y' else (d,p[0],p[1])
    vs=[point(p,d) for d in (-depth/2,depth/2) for loop in (outer,inner) for p in loop]
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
               (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    return vs,fs


def mesh_obj(name, geometry, pos, mat, parent=None, bevel=.0004):
    """输入名称、几何、位置、材质与父级，返回带真实米制UV的新对象。"""
    me=bpy.data.meshes.new(name)
    me.from_pydata(*[geometry[0],[],geometry[1]])
    me.update()
    bm=bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me)
    bpy.data.collections['AST_window_wall_left'].objects.link(ob)
    ob.location=pos
    me.materials.append(mat)
    uv=me.uv_layers.new(name='MetalMeters')
    for p in me.polygons:
        axes=sorted(range(3),key=lambda i:abs(p.normal[i]))[:2]
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]],co[axes[1]])
    if bevel:
        mod=ob.modifiers.new('Bevel','BEVEL'); mod.width=bevel; mod.segments=3
        mod=ob.modifiers.new('WeightedNormal','WEIGHTED_NORMAL'); mod.keep_sharp=True
    ob[REV]=True
    if parent:
        # 原点已经为世界坐标；绑定时保持可见位置，不改现有控制器。
        bpy.context.view_layer.update()
        ob.parent=parent
        ob.matrix_parent_inverse=parent.matrix_world.inverted()
    return ob


def box_geo(size):
    """输入XYZ尺寸，返回中心位于原点的长方体网格。"""
    x,y,z=[v/2 for v in size]
    return ([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],
            [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


def combine(chunks):
    """输入多个(几何,偏移)，返回合并后的网格，保留零件间隙。"""
    vs=[]; fs=[]
    for (v,f),off in chunks:
        n=len(vs); vs.extend(tuple(p[i]+off[i] for i in range(3)) for p in v)
        fs.extend(tuple(n+j for j in face) for face in f)
    return vs,fs


def crescent_cup():
    """返回单一封闭流形的半圆锁杯；4mm径向壁厚、2mm背板，避免交叠圆管拼形。"""
    count=41
    loops=[]
    for radius,depth in ((.020,-.005),(.020,.002),(.016,-.005),(.016,0)):
        loops.extend((radius*math.cos(math.radians(90+i*180/40)),depth,
                      radius*math.sin(math.radians(90+i*180/40))) for i in range(count))
    faces=[]
    for i in range(count-1):
        faces += [(i,i+1,count+i+1,count+i),
                  (i,2*count+i,2*count+i+1,i+1),
                  (2*count+i,3*count+i,3*count+i+1,2*count+i+1)]
    faces += [tuple(range(count,2*count)),tuple(reversed(range(3*count,4*count))),
              (0,count,2*count-1,count-1,3*count-1,4*count-1,3*count,2*count)]
    return loops,faces


def replace(old, geometry, pos, parent=None, material=None, bevel=.0004):
    """输入现有五金与新几何，返回同名替代件；不修改共享旧网格和材质节点。"""
    name=old.name
    mat=material or old.data.materials[0]
    assert old.animation_data is None, name
    bpy.data.objects.remove(old,do_unlink=True)
    return mesh_obj(name,geometry,pos,mat,parent,bevel)


def pocket(stile, pos):
    """给窗梃添加16×105mm可编辑布尔凹槽；隐藏切割体跟随窗扇，保留修改器。"""
    stile.data=stile.data.copy()
    cutter=mesh_obj('CUT pull pocket '+stile.name,prism(rounded(.016,.105,.003),.009,'X'),pos,
                    bpy.data.materials['ARC SD graphite EPDM'],parent=stile,bevel=0)
    cutter.hide_render=True; cutter.hide_viewport=True; cutter.hide_set(True); cutter.display_type='WIRE'
    cutter['purpose']='Editable cutter for recessed finger pull; keep hidden'
    bpy.context.view_layer.update()
    mod=stile.modifiers.new('Boolean','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
    # 布尔在倒角之前求值；切割体与修改器保留，便于用户继续硬表面建模。
    bpy.context.view_layer.objects.active=stile
    with bpy.context.temp_override(object=stile,active_object=stile,selected_objects=[stile],selected_editable_objects=[stile]):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)


def fingerprint():
    """返回原有对象的变换、数据名和父级，供非目标对象保护验证。"""
    return {o.name:{'matrix':[list(r) for r in o.matrix_world],'data':o.data.name if o.data else None,
                    'parent':o.parent.name if o.parent else None} for o in bpy.context.scene.objects}


def apply_correction():
    """对实时/后台当前建筑源实施六组结构修正，返回修改清单及保护检查。"""
    coll=bpy.data.collections['AST_window_wall_left']
    assert not any(o.get(REV) for o in coll.objects), 'Already corrected'
    before=fingerprint(); original_selection=[o.name for o in bpy.context.selected_objects]
    active=bpy.context.view_layer.objects.active
    active_name=active.name if active else None
    ctrl=bpy.data.objects['ctrl_window_left_04']
    saved_y=ctrl.location.y
    modified=set(); groups=[]
    steel=bpy.data.materials['ARC SD satin aluminium']
    rubber=bpy.data.materials['ARC SD graphite EPDM']
    lower=[o for o in coll.objects if o.name.startswith('WIN sliding sash stile') and o.dimensions.z>1]
    old_centers={o.name:center(o) for o in list(coll.objects) if not o.hide_render}
    bases=sorted([o for o in coll.objects if o.name.startswith('ARC crescent lock escutcheon') and not o.hide_render],key=lambda o:old_centers[o.name].y)
    assert len(bases)==6
    for index,base in enumerate(bases):
        bc=old_centers[base.name]
        inner=min(lower,key=lambda o:(center(o)-Vector((-3.974,bc.y,1.794))).length)
        suffix=base.name[len('ARC crescent lock escutcheon'):]
        # 对侧窗扇由对应拉手追踪，兼容用户已将第四窗向-Y移开的状态。
        outer_pull_name='WIN pull grip'+('.%03d'%(index*2+1))
        outer_pull=bpy.data.objects[outer_pull_name]
        outer=min(lower,key=lambda o:(center(o)-Vector((-4.026,center(outer_pull).y,1.794))).length)
        ic=center(inner); oc=center(outer)
        x=ic.x-.0075; y=ic.y; z=bc.z
        oldparts=[o for o in list(coll.objects) if not o.hide_render and o.name.startswith('ARC ') and
                  (old_centers.get(o.name,Vector((100,100,100)))-bc).length<.09 and
                  any(s in o.name for s in ('lock','crescent','latch','screw','drive recess'))]
        modified.update(o.name for o in oldparts)
        mat_by={o.name:o.data.materials[0] for o in oldparts}
        for ob in oldparts: bpy.data.objects.remove(ob,do_unlink=True)
        base_new=mesh_obj(base_name:='ARC crescent lock escutcheon'+suffix,
                          prism(rounded(.0233,.066,.003),.003), (x,y+.015,z),steel,inner)
        base_new['reference_url']=REF_LOCK; base_new['mounting']='Inner meeting stile side face; shaft parallel to slide axis Y'
        # 轴沿Y，底座贴侧面；杯状锁片处于两轨之间，不再用圆管模拟锁片。
        axle=mesh_obj('ARC lock axle'+suffix,prism([(math.cos(a*math.tau/48)*.0055,math.sin(a*math.tau/48)*.0055) for a in range(48)],.009),
                      (x,y+.021,z),steel,inner)
        rig=bpy.data.objects.new('ctrl_window_lock_%02d'%(index+1),None); coll.objects.link(rig)
        rig.location=(x,y+.025,z); rig.empty_display_type='CIRCLE'; rig.empty_display_size=.03
        rig.parent=inner; rig.matrix_parent_inverse=inner.matrix_world.inverted()
        rig.lock_location=(True,True,True); rig.lock_rotation=(True,False,True); rig.lock_scale=(True,True,True)
        rig['operation']='Rotation Y: 0 degrees latched / 180 degrees released; release before sliding'
        rig[REV]=True
        camgeo=crescent_cup()
        cam=mesh_obj('ARC crescent cam'+suffix,camgeo,(x,y+.025,z),mat_by.get('ARC crescent cam'+suffix,steel),rig,.00035)
        cam['reference_url']=REF_LOCK
        handle_poly=rounded(.0151,.040,.0025)
        handle=mesh_obj('ARC curved latch handle'+suffix,prism(handle_poly,.004),
                        (x+.003,y+.030,z-.018),mat_by.get('ARC curved latch handle'+suffix,steel),rig,.00065)
        # 40mm螺孔间距与实物图一致；槽口为独立低位几何。
        for j,zz in enumerate((z-.020,z+.020)):
            screw=mesh_obj('WIN lock screw %02d %d'%(index+1,j),prism([(math.cos(a*math.tau/32)*.0025,math.sin(a*math.tau/32)*.0025) for a in range(32)],.0012),(x,y+.017,zz),steel,inner,.00015)
            mesh_obj('WIN lock screw slot %02d %d'%(index+1,j),box_geo((.0035,.0002,.0006)),(x,y+.0177,zz),rubber,inner,.00008)
        # 扣座固定在外轨窗扇上；弯折薄板跨向轨道间隙，突出量受内扇背面限制。
        front=oc.x+.0185
        keepergeo=combine([(box_geo((.0015,.016,.042)),(0,0,0)),
                           (box_geo((.012,.002,.014)),(.006,-.004,0)),
                           (box_geo((.012,.002,.014)),(.006,.022,0)),
                           (box_geo((.002,.028,.014)),(.011, .009,0))])
        keeper=mesh_obj('ARC lock keeper'+suffix,keepergeo,(front+.00075,oc.y,z),steel,outer,.0003)
        keeper['reference_url']='https://parts.ykkap.co.jp/download/HHW11-050.pdf'
        keeper['fit_note']='Keeper stand-off adapted to existing 52mm track centres; not a certified product replica'
        for j,zz in enumerate((z-.010,z+.010)):
            mesh_obj('WIN keeper screw %02d %d'%(index+1,j),prism([(math.cos(a*math.tau/32)*.002,math.sin(a*math.tau/32)*.002) for a in range(32)],.001,'X'),(front+.0018,oc.y,zz),steel,outer,.0001)
        bpy.context.view_layer.update()
        # 当前已经打开的窗保持开度，并将它对应的月牙锁置于解锁状态。
        opened=outer.parent==ctrl and abs(saved_y)>.001
        if opened: rig.rotation_euler.y=math.pi
        groups.append({'index':index+1,'base':base_new.name,'cam':cam.name,'handle':handle.name,'rig':rig.name,'keeper':keeper.name,
                       'inner_stile':inner.name,'outer_stile':outer.name,'open':opened})
    # 所有下窗拉手采用26×134mm薄边框与真实凹槽，不在窗梃表面叠实心小块。
    pulls=sorted([o for o in coll.objects if o.name.startswith('WIN pull grip')],key=lambda o:o.name)
    assert len(pulls)==12
    for grip in pulls:
        gc=center(grip)
        stile=min(lower,key=lambda o:abs(center(o).y-gc.y)+abs(center(o).x-(gc.x-.035)))
        sc=center(stile); face=sc.x+.0185
        suffix=grip.name[len('WIN pull grip'):]
        recess=bpy.data.objects['WIN pull recess'+suffix]
        modified.update((grip.name,recess.name,stile.name))
        pocket(stile,(face-.001,sc.y,gc.z))
        # 金属薄边前凸0.8mm，槽底在框面下4.8mm；外轨拉手不会碰到内轨窗框。
        new=replace(grip,ring(rounded(.026,.134,.004),rounded(.016,.105,.003),.0008,'X'),(face+.0004,sc.y,gc.z),stile,steel,.0002)
        new['reference_url']=REF_PULL
        replace(recess,prism(rounded(.0158,.1048,.0028),.0005,'X'),(face-.0048,sc.y,gc.z),stile,steel,.00015)
    bpy.context.view_layer.update()
    after=fingerprint()
    errors=[]
    for name,data in before.items():
        if name not in modified and after.get(name)!=data: errors.append(name)
    assert not errors,errors
    assert ctrl.location.y==saved_y
    # 控制器仍由同一窗扇负责；更新递归部件清单，避免保留用户已删除扣座的旧列表。
    ctrl['controlled_parts']=json.dumps([o.name for o in ctrl.children_recursive],ensure_ascii=False)
    for ob in bpy.context.selected_objects: ob.select_set(False)
    for name in original_selection:
        if name in bpy.context.view_layer.objects: bpy.data.objects[name].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects.get(active_name) if active_name else ctrl
    report={'groups':groups,'modified_objects':sorted(modified),'non_target_changed':errors,'controller_y':saved_y,
            'preserved_original_count':len(before)-len(modified),'reference_lock':REF_LOCK,'reference_pull':REF_PULL}
    return report


def evaluated_bvh(obj):
    """输入对象，返回带修改器和世界变换的BVH，用于实际表面碰撞检查。"""
    eo=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=eo.to_mesh()
    tree=BVHTree.FromPolygons([eo.matrix_world @ v.co for v in me.vertices],[list(p.vertices) for p in me.polygons])
    eo.to_mesh_clear(); return tree


def validate_motion(report):
    """在候选内检查第四窗解锁后0至60cm滑动；恢复用户开度和锁角，返回交叉面数量。"""
    ctrl=bpy.data.objects['ctrl_window_left_04']; saved=ctrl.location.y
    group=next(g for g in report['groups'] if g['open'])
    rig=bpy.data.objects[group['rig']]; angle=rig.rotation_euler.y
    fixed=[bpy.data.objects[group['inner_stile']],bpy.data.objects['WIN clear 5mm glass.004'],bpy.data.objects[group['cam']]]
    moving=[bpy.data.objects[group['keeper']],bpy.data.objects['WIN pull grip.003'],bpy.data.objects[group['outer_stile']]]
    records=[]
    try:
        rig.rotation_euler.y=math.pi
        for shift in (0,-.05,-.2170781195,-.4,-.6):
            ctrl.location.y=shift; bpy.context.view_layer.update()
            hits=[]
            for a in moving:
                for b in fixed:
                    count=len(evaluated_bvh(a).overlap(evaluated_bvh(b)))
                    if count: hits.append({'moving':a.name,'fixed':b.name,'faces':count})
            records.append({'y':shift,'intersections':hits})
    finally:
        ctrl.location.y=saved; rig.rotation_euler.y=angle; bpy.context.view_layer.update()
    return records


def main():
    """后台入口：制作候选并验证；不覆盖正式建筑文件。"""
    report=apply_correction()
    report['motion']=validate_motion(report)
    REVIEW.mkdir(exist_ok=True,parents=True)
    (REVIEW/'candidate_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'candidate.blend'),relative_remap=True,check_existing=False)
    print(json.dumps({'groups':len(report['groups']),'motion':report['motion'],'protected':report['preserved_original_count']}))


if __name__=='__main__':
    main()
