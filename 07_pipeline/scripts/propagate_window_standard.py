"""将当前外窗分件/烘焙五金推广到同类走廊推拉窗，保留开度并移除凸起排水占位块。

输入当前建筑源；输出cache候选和保护清单。固定窗洞、窗扇世界位置和原有控制器。
右侧窗按安装侧镜像五金，沿用各窗宽高，46mm轨距与52mm模板的差异在安装偏移中适配。
"""
import bpy, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/window_propagation'
OUT=ROOT/'06_review/window_propagation'
SCOPES=['AST_window_wall_left','AST_window_wall_corridor','AST_classroom_corridor']


def center(o):
    """输入对象，返回世界包围盒中心，不依赖历史原点。"""
    return sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8


def fingerprint():
    """记录所有对象的世界位置、父级、数据和可见性，验证非目标保护。"""
    return {o.name:{'matrix':[[round(x,6) for x in r] for r in o.matrix_world],
                    'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,
                    'hide_render':o.hide_render,'hide_viewport':o.hide_viewport} for o in bpy.context.scene.objects}


def parent_keep(o,parent):
    """设置父级并保持世界变换；用于五金附着所属窗扇，不移动既有窗扇。"""
    world=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_world=world


def clone(source,name,coll,matrix,parent=None):
    """以当前模板的真实网格/UV/材质创建部件，保留共享数据，映射到目标安装位置。"""
    ob=source.copy();ob.name=name;ob.parent=None;coll.objects.link(ob);ob.matrix_world=matrix@source.matrix_world
    ob['window_standard']='2026-09-28';ob['template_object']=source.name
    if parent:parent_keep(ob,parent)
    return ob


def profile(ob,template):
    """复用模板分件的几何和涂层，适配原窗宽高；保持目标对象和窗洞位置。"""
    dims=ob.dimensions.copy();source_dims=template.dimensions.copy()
    # 框宽高保持，以原窗扇安装厚度适配轨道，不整体缩放五金图集。
    me=template.data.copy();lo=Vector(tuple(min(v.co[i] for v in me.vertices) for i in range(3)))
    hi=Vector(tuple(max(v.co[i] for v in me.vertices) for i in range(3)));mid=(lo+hi)/2
    scl=ob.matrix_world.to_scale()
    for v in me.vertices:
        v.co=Vector(tuple((v.co[i]-mid[i])*dims[i]/max(hi[i]-lo[i],1e-9)/abs(scl[i]) for i in range(3)))
    ob.data=me;ob['window_standard']='2026-09-28';ob['template_object']=template.name
    # 目标保持自己的倒角宽度/位置；两个源均为等截面窗框件。


def apply():
    """执行范围内统一；输出候选、删除对象和窗扇/控制器保护结果。"""
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    before=fingerprint();source_hash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    src_inner=bpy.data.objects['WIN sliding sash stile.001'];src_outer=bpy.data.objects['WIN sliding sash stile.004']
    origin=Vector((center(src_inner).x,center(src_inner).y,1.61));outer_origin=Vector((center(src_outer).x,center(src_outer).y,1.61))
    mirror=Matrix.Diagonal((-1,1,1,1));modified=set();removed=[];added=[];groups=[];profile_rows=[]
    # 当前可见推拉窗；历史Archive内的旧模型保留，避免改变归档。
    for cname in SCOPES:
        coll=bpy.data.collections[cname]
        for ob in list(coll.objects):
            if not ob.hide_render and ob.name.startswith(('WIN drainage slot','REF drainage slot','ARC track drain opening','ARC drain hood')):
                removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
    mapping={'REF perimeter frame stile':'WIN perimeter stile','REF perimeter frame rail':'WIN perimeter rail',
             'REF sliding sash stile':'WIN sliding sash stile','REF sliding sash rail':'WIN sliding sash rail',
             'REF upper sash stile':'WIN sliding sash stile.002','REF upper sash rail':'WIN sliding sash rail.002',
             'REF glazing bead stile':'WIN glazing bead stile','REF glazing bead rail':'WIN glazing bead rail',
             'REF EPDM seal stile':'WIN EPDM seal stile','REF EPDM seal rail':'WIN EPDM seal rail'}
    for cname in SCOPES[1:]:
        coll=bpy.data.collections[cname]
        for ob in list(coll.objects):
            family=ob.name.split('.')[0]
            if not ob.hide_render and family in mapping:
                profile(ob,bpy.data.objects[mapping[family]]);modified.add(ob.name);profile_rows.append(ob.name)
        bpy.context.view_layer.update()
        lower=[o for o in coll.objects if o.name.startswith('REF sliding sash stile') and not o.hide_render]
        bases=sorted([o for o in coll.objects if o.name.startswith('ARC crescent lock escutcheon') and not o.hide_render],key=lambda o:center(o).y)
        pulls=[o for o in coll.objects if o.name.startswith('REF recessed finger pull') and not o.hide_render]
        for index,old in enumerate(bases):
            old_name=old.name;suffix=old_name[len('ARC crescent lock escutcheon'):];bc=center(old)
            inner=min(lower,key=lambda o:(center(o)-Vector((bc.x+.026,bc.y,center(o).z))).length)
            ic=center(inner)
            outer=min([o for o in lower if center(o).x>ic.x+.025],key=lambda o:abs(center(o).y-ic.y))
            oc=center(outer)
            z=bc.z
            # 侧装锁沿Y，镜像到教室/走廊右侧。窄6mm的轨距将锁整体内收3mm。
            shift=(.052-abs(oc.x-ic.x))*.5
            trans=Matrix.Translation(Vector((ic.x-shift,ic.y,z)))@mirror@Matrix.Translation(-origin)
            out_trans=Matrix.Translation(Vector((oc.x,oc.y,z)))@mirror@Matrix.Translation(-outer_origin)
            doomed=[o for o in coll.objects if not o.hide_render and o.name.startswith('ARC ') and (center(o)-bc).length<.10 and any(t in o.name for t in ('lock','crescent','latch','screw','drive recess'))]
            for ob in doomed:removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
            rig=bpy.data.objects.new('ctrl_window_lock'+suffix,None);coll.objects.link(rig)
            rig.matrix_world=trans@bpy.data.objects['ctrl_window_lock_01'].matrix_world;rig.empty_display_type='CIRCLE';rig.empty_display_size=.03
            rig.lock_location=(True,True,True);rig.lock_rotation=(True,False,True);rig.lock_scale=(True,True,True)
            parent_keep(rig,inner);added.append(rig.name)
            rig['operation']='Rotate local Y to release; window opening is unchanged'
            parts=[]
            for stem,parent in [('ARC crescent lock escutcheon',inner),('ARC lock axle',inner),('ARC crescent cam',rig),('ARC curved latch handle',rig)]:
                ob=clone(bpy.data.objects[stem+'.039'],stem+suffix,coll,trans,parent);parts.append(ob.name);added.append(ob.name)
            keeper=clone(bpy.data.objects['ARC lock keeper.039'],'ARC lock keeper'+suffix,coll,out_trans,outer);added.append(keeper.name)
            for j in range(2):
                for stem in ['WIN lock screw','WIN lock screw slot']:
                    ob=clone(bpy.data.objects[f'{stem} 01 {j}'],f'{stem}{suffix} {j}',coll,trans,inner);added.append(ob.name)
                ob=clone(bpy.data.objects[f'WIN keeper screw 01 {j}'],f'WIN keeper screw{suffix} {j}',coll,out_trans,outer);added.append(ob.name)
            groups.append({'base':old_name,'collection':cname,'inner':inner.name,'outer':outer.name,'rig':rig.name,'keeper':keeper.name,'parts':parts,'track_gap':oc.x-ic.x})
        # 拉手正对室内面，真实凹槽尺寸、深度与模板一致；随各自窗梃移动。
        for old in pulls:
            pc=center(old);name=old.name
            stile=min(lower,key=lambda o:abs(center(o).y-pc.y)+abs(center(o).x-(pc.x+.023)))
            sc=center(stile);face=sc.x-stile.dimensions.x/2
            source_grip=bpy.data.objects['WIN pull grip'];source_stile=source_grip.parent
            sg=center(source_grip);ss=center(source_stile)
            source_anchor=Vector((ss.x+source_stile.dimensions.x/2,ss.y,sg.z))
            target_anchor=Vector((face,sc.y,pc.z));transform=Matrix.Translation(target_anchor)@mirror@Matrix.Translation(-source_anchor)
            bpy.data.objects.remove(old,do_unlink=True);removed.append(name)
            grip=clone(source_grip,name,coll,transform,stile);added.append(grip.name)
            floor=clone(bpy.data.objects['WIN pull recess'],name+' / recess',coll,transform,stile);added.append(floor.name)
            source_cut=next(m.object for m in source_stile.modifiers if m.type=='BOOLEAN' and m.object)
            cut=clone(source_cut,'CUT pocket '+name,coll,transform,stile);cut.hide_render=True;cut.hide_viewport=True;cut.hide_set(True);added.append(cut.name)
            mod=stile.modifiers.new('Boolean','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
            # 新切割体在倒角前，保证开口边缘仍有高光。
            with bpy.context.temp_override(object=stile,active_object=stile,selected_objects=[stile],selected_editable_objects=[stile]):
                bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
            modified.add(stile.name)
    bpy.context.view_layer.update();after=fingerprint()
    protected=[n for n in before if n not in removed and n not in modified]
    changes=[n for n in protected if before[n]!=after.get(n)]
    moved=[n for n in before if n not in removed and before[n]['matrix']!=after[n]['matrix']]
    assert not changes,changes[:10];assert not moved,moved[:10]
    assert all(bpy.data.objects[g['parts'][2]].data.materials[0].name.startswith('Hardware / Satin metal baked') for g in groups)
    # 图集原样复用，未缩放烘焙UV；只有镜像安装矩阵及窗框尺寸适配。
    report={'input_hash':source_hash,'groups':groups,'new_lock_groups':len(groups),'profile_count':len(profile_rows),
            'removed':removed,'added':added,'modified':sorted(modified),'protected_count':len(protected),'unexpected_changes':changes,
            'existing_objects_moved':moved,'source_control_y':bpy.data.objects['ctrl_window_left_04'].location.y,
            'source_lock_y':bpy.data.objects['ctrl_window_lock_02'].rotation_euler.y}
    (OUT/'candidate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (CACHE/'before_fingerprint.json').write_text(json.dumps(before,ensure_ascii=False),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'candidate.blend'),relative_remap=True)
    print(json.dumps({k:report[k] for k in ['new_lock_groups','profile_count','protected_count','existing_objects_moved']}))


if __name__=='__main__':apply()
