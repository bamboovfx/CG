"""以最新正式镜头建立单文件教室候选，保留实例共享并暴露材质编辑入口。"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/classroom_pipeline_migration_20260929'
CACHE.mkdir(parents=True,exist_ok=True)


def inventory():
    """记录制作帧、源对象矩阵、实例、动作及材质，供迁移前后验证。"""
    s=bpy.context.scene
    return {'frame':s.frame_current,'range':[s.frame_start,s.frame_end],'fps':s.render.fps,
      'camera':s.camera.name,'camera_matrix':[list(row) for row in s.camera.matrix_world],
      'world':s.world.name if s.world else None,
      'actions':sorted(a.name for a in bpy.data.actions if not a.library),
      'instances':{o.name:{'collection':o.instance_collection.name,'matrix':[list(row) for row in o.matrix_world]} for o in s.objects if o.instance_collection},
      'local':{o.name:{'matrix':[list(row) for row in o.matrix_world],'parent':o.parent.name if o.parent else None} for o in s.objects if not o.library},
      'counts':{name:len(getattr(bpy.data,name)) for name in ['objects','meshes','materials','images','collections']},
      'materials':{m.name:len(m.node_tree.nodes) if m.node_tree else None for m in bpy.data.materials}}


def expose_blackboard():
    """将单实例黑板放入现有镜头，保持视觉世界变换，并允许直接选中书写面。"""
    s=bpy.context.scene;c=bpy.data.collections['AST_chalkboard']
    matches=[o for o in s.objects if o.instance_collection==c]
    assert len(matches)==1,len(matches)
    inst=matches[0];items=set(c.all_objects)
    assert all(len(o.users_collection)==1 for o in items)
    transform=inst.matrix_world @ Matrix.Translation(-c.instance_offset)
    before={o.name:[list(row) for row in transform@o.matrix_world] for o in items}
    # 仅根对象承受变换；子物体继续跟随父级，避免双重位移。
    for o in items:
        if o.parent not in items:o.matrix_world=transform@o.matrix_world
    s.collection.children.link(c)
    bpy.data.objects.remove(inst,do_unlink=True)
    bpy.context.view_layer.update()
    after={o.name:[list(row) for row in o.matrix_world] for o in items}
    errors=[n for n in before if max(abs(before[n][i][j]-after[n][i][j]) for i in range(4) for j in range(4))>1e-4]
    assert not errors,errors[:10]
    board=bpy.data.objects['Unique wiped writing surface']
    for o in bpy.context.selected_objects:o.select_set(False)
    board.select_set(True);bpy.context.view_layer.objects.active=board
    return {'collection':c.name,'objects':len(items),'world_matrix_errors':errors,'selected':board.name,
       'material':board.active_material.name}


def material_controls():
    """为每种实际材质创建不参与渲染的控制片，供Outliner搜索后直接编辑节点。"""
    c=bpy.data.collections.new('LOOKDEV / material selectors');bpy.context.scene.collection.children.link(c)
    names=[]
    for index,mat in enumerate(sorted(bpy.data.materials,key=lambda m:m.name.casefold())):
        if not mat.use_nodes:continue
        mesh=bpy.data.meshes.new('LOOKDEV selector mesh')
        mesh.from_pydata([(0,0,0),(.06,0,0),(0,.06,0)],[],[(0,1,2)])
        mesh.materials.append(mat)
        o=bpy.data.objects.new('MAT / '+mat.name,mesh);c.objects.link(o)
        o.location=(1000+(index%16)*.08,(index//16)*.08,0)
        o.hide_render=True
        o['purpose']='Select this object in Outliner to edit its shared material under the shot lighting.'
        names.append(o.name)
    return {'collection':c.name,'count':len(names),'blackboard_selector':next((n for n in names if n=='MAT / Blackboard / Aged baked green coating'),None)}


def main():
    """从当前已保存正式镜头快照，输出独立候选和结构证据。"""
    source=Path(bpy.data.filepath)
    assert source.name=='drop_sq010_sh010_shot.blend'
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    before=inventory()
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'source_before.blend'),copy=True,relative_remap=True)
    # 本地化数据块，而非逐实例转为独立网格；保留贴图、集合实例及动画对象。
    bpy.ops.object.make_local(type='ALL')
    after_local=inventory()
    for key in ['counts','instances','actions','camera_matrix','frame','range','fps','world']:
        if key in ['counts','materials']:continue
        assert before[key]==after_local[key],key
    assert before['counts']==after_local['counts']
    assert all(before['local'][n]==after_local['local'].get(n) for n in before['local'])
    assert all(o.library is None for o in bpy.data.objects)
    assert all(m.library is None for m in bpy.data.materials)
    board=expose_blackboard();controls=material_controls()
    output=inventory()
    assert output['frame']==before['frame'] and output['actions']==before['actions']
    assert board['selected'] in bpy.context.scene.objects
    assert bpy.context.view_layer.objects.active.active_material.is_editable
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'candidate.blend'),relative_remap=True)
    report={'source_hash':source_hash,'before':before,'after_local':after_local,'after':output,
            'board':board,'controls':controls,'candidate':str(CACHE/'candidate.blend')}
    (CACHE/'candidate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'board':board,'controls':controls,'instances_preserved':len(output['instances']),'source_hash':source_hash},ensure_ascii=False))


if __name__=='__main__':main()
