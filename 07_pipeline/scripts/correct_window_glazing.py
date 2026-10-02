"""修正窗扇玻璃装配：嵌槽、U形胶条与金属压条；保留对象变换/父级/五金。

输入当前建筑源；只处理三个活动集合的84块同类玻璃，历史Archive不动。
截面为参考实际装配关系的CG适配尺寸，并非特定厂商的可制造工程图。
"""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/window_glazing'
OUT=ROOT/'06_review/window_glazing'
SCOPES=['AST_window_wall_left','AST_window_wall_corridor','AST_classroom_corridor']


def center(o):
    """输入对象，返回世界包围盒中心。"""
    return sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8


def fingerprint():
    """记录对象几何/变换/材质，供候选与实时源合并前检查。"""
    result={}
    for o in bpy.data.objects:
        geom=None
        if o.type=='MESH':
            geom=hashlib.sha256(str([(tuple(v.co)) for v in o.data.vertices]).encode()).hexdigest()
        result[o.name]={'matrix':[[round(x,6) for x in r] for r in o.matrix_world],
            'parent':o.parent.name if o.parent else None,'geom':geom,
            'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],
            'hide':[o.hide_render,o.hide_viewport]}
    return result


def mesh_world(o,verts,faces,bevel=None):
    """以世界顶点替换单对象网格，保留矩阵及材质；生成等密度面UV。"""
    inv=o.matrix_world.inverted();me=bpy.data.meshes.new(o.data.name+' / glazing')
    me.from_pydata([inv@Vector(v) for v in verts],[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    for m in o.data.materials:me.materials.append(m)
    # 等米制密度的分面UV；此处涂层/胶条不使用五金图集，不改烘焙材质。
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(v[axes[0]],v[axes[1]])
    o.data=me;o['glazing_revision']='2026-09-28'
    if bevel is not None:
        for m in o.modifiers:
            if m.type=='BEVEL':m.width=bevel;m.segments=3


def extrusion(o,gc,axis,sign,opening,profile,length,miter=False,bevel=.00015):
    """沿窗边挤出X/径向截面；axis为边法向，45度接角用于胶条。"""
    tangent=3-axis;verts=[]
    for end in [-1,1]:
        for x,r in profile:
            v=gc.copy();v.x+=x;v[axis]+=sign*(opening+r)
            v[tangent]+=end*(length/2+(r if miter else 0));verts.append(v)
    n=len(profile);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh_world(o,verts,faces,bevel)


def apply(save=True):
    """修正所有活动窗，验证矩阵/非目标几何保护；可用于背景候选或实时源。"""
    OUT.mkdir(parents=True,exist_ok=True)
    before=fingerprint();modified=set();removed=[];groups=[]
    # 先按旧几何匹配分件，再改网格，避免逐步改动影响查找。
    for cn in SCOPES:
        objs=[o for o in bpy.data.collections[cn].objects if not o.hide_render]
        glasses=[o for o in objs if o.name.startswith(('WIN clear 5mm glass','REF clear glazing'))]
        prefix='WIN' if cn==SCOPES[0] else 'REF'
        seals=[o for o in objs if o.name.startswith(prefix+' EPDM seal')]
        beads=[o for o in objs if o.name.startswith(prefix+' glazing bead')]
        frames=[o for o in objs if o.name.startswith(prefix+' sliding sash')]
        for g in glasses:
            gc=center(g);gd=g.dimensions.copy();parts=[]
            for axis,stem in [(1,'stile'),(2,'rail')]:
                tangent=3-axis
                for sign in [-1,1]:
                    pred=gc.copy();pred[axis]+=sign*gd[axis]/2
                    candidates=[o for o in frames if stem in o.name and abs(center(o).x-gc.x)<.001 and abs(center(o)[tangent]-gc[tangent])<.002]
                    f=min(candidates,key=lambda o:(center(o)-pred).length)
                    fc=center(f);opening=abs(fc[axis]-gc[axis])-f.dimensions[axis]/2
                    s=min([o for o in seals if stem in o.name],key=lambda o:(center(o)-pred).length)
                    bs=sorted([o for o in beads if stem in o.name],key=lambda o:(center(o)-pred).length)[:2]
                    assert abs(center(s).x-gc.x)<.001,(g.name,s.name)
                    assert all(abs(center(b)[axis]-fc[axis])<.025 for b in bs)
                    parts.append(dict(axis=axis,sign=sign,opening=opening,frame=f,seal=s,beads=bs,
                        frame_dims=f.dimensions.copy(),bead_centers=[center(b) for b in bs]))
            groups.append(dict(glass=g,center=gc,dims=gd,parts=parts,collection=cn))
    assert len(groups)==84,len(groups)
    used=[p['seal'].name for g in groups for p in g['parts']]
    assert len(set(used))==336,'每个密封分件只能匹配一块玻璃'
    records=[]
    for group in groups:
        g=group['glass'];gc=group['center'];parts=group['parts']
        half={a:sum(p['opening'] for p in parts if p['axis']==a)/2 for a in [1,2]}
        # 玻璃嵌入边框6mm；厚度保持5mm，填掉此前悬空接缝。
        ext=Vector((group['dims'].x/2,half[1]+.006,half[2]+.006))
        verts=[gc+Vector((x*ext.x,y*ext.y,z*ext.z)) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1),(1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1)]]
        mesh_world(g,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)],.00008);modified.add(g.name)
        for p in parts:
            a=p['axis'];sg=p['sign'];op=p['opening'];t=3-a;f=p['frame'];fd=p['frame_dims'];h=fd.x/2;w=fd[a]
            # 窗扇内侧做真实开口槽；外表面保留原宽度和现有拉手布尔。
            fp=[(-h,.004),(-.0043,.004),(-.0043,.008),(.0043,.008),(.0043,.004),(h,.004),(h,w),(-h,w)]
            extrusion(f,gc,a,sg,op,fp,fd[t],bevel=.0002);modified.add(f.name)
            # 胶条为包覆玻璃边缘的U槽，绝非横跨整个窗框厚度的实心条。
            gh=group['dims'].x/2
            sp=[(-.0042,-.0012),(-gh,-.0012),(-gh,.006),(gh,.006),(gh,-.0012),(.0042,-.0012),(.0042,.007),(-.0042,.007)]
            extrusion(p['seal'],gc,a,sg,op,sp,2*half[t],miter=True,bevel=.00008);modified.add(p['seal'].name)
            for b,bc in zip(p['beads'],p['bead_centers']):
                side=1 if bc.x>gc.x else -1
                bp=[(side*(h+.002),.004),(side*(h+.002),-.0004),(side*.0043,0),(side*.0043,.004)]
                extrusion(b,gc,a,sg,op,bp,2*half[t],miter=True,bevel=.0001);modified.add(b.name)
        records.append({'glass':g.name,'collection':group['collection'],'opening_half':half,'seal_depth_mm':8.4,'visible_lip_mm':1.2,'glass_bite_mm':6})
    for cn in SCOPES:
        for o in list(bpy.data.collections[cn].objects):
            if not o.hide_render and o.name.startswith('REF rubber sash stop'):
                removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update();after=fingerprint()
    protected=[n for n in before if n not in removed and n not in modified]
    unexpected=[n for n in protected if before[n]!=after.get(n)]
    moved=[n for n in before if n not in removed and before[n]['matrix']!=after[n]['matrix']]
    assert not unexpected,unexpected[:10]
    assert not moved,moved[:10]
    report={'panes':records,'modified':sorted(modified),'removed':removed,'protected_count':len(protected),'unexpected_changes':unexpected,'moved':moved}
    if save:
        (CACHE/'baseline.json').write_text(json.dumps(before),encoding='utf8')
        (OUT/'candidate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'candidate.blend'),relative_remap=True)
    return report


if __name__=='__main__':
    r=apply();print(json.dumps({'panes':len(r['panes']),'removed':len(r['removed']),'modified':len(r['modified']),'unexpected':r['unexpected_changes']}))
