"""重开单文件候选，验证素材依赖与共享材质/镜头例外的真实Blender数据关系。"""
import bpy,json,hashlib,sys,os
from pathlib import Path
ROOT=Path('D:/00_projects/10_CG/Shot_Test');CACHE=ROOT/'07_pipeline/cache/classroom_pipeline_migration_20260929'
data=json.loads((CACHE/'candidate.json').read_text(encoding='utf8'))
scene=bpy.context.scene;board=bpy.data.objects['Unique wiped writing surface'];material=board.active_material


def active_instances(s):
    """按实例对象名记录集合与矩阵，排除刻意实体化的唯一黑板。"""
    return {o.name:{'collection':o.instance_collection.name,'matrix':[list(r) for r in o.matrix_world]} for o in s.objects if o.instance_collection}


def check_material_target():
    """实际写回本地材质一个微量测试值，并立即恢复，证明节点可编辑。"""
    assert material.is_editable and material.node_tree.is_editable
    for n in material.node_tree.nodes:
        for socket in n.inputs:
            if socket.is_linked or not hasattr(socket,'default_value'):continue
            old=socket.default_value
            if not isinstance(old,float):continue
            try:
                socket.default_value=old+.001
                changed=abs(socket.default_value-old)>.0001
                socket.default_value=old
                if changed:return {'node':n.name,'socket':socket.name,'restored':abs(socket.default_value-old)<1e-8}
            except (AttributeError,ValueError,TypeError):continue
    raise AssertionError('黑板节点没有可编辑的未连线数值输入')


def second_scene_probe():
    """用临时第二场景检查共用材质和局部例外；测试完成后不保存。"""
    original=scene
    other=bpy.data.scenes.new('TEST / second classroom shot')
    other.world=original.world.copy()
    other.collection.children.link(bpy.data.collections['AST_window_wall_left']) if 'AST_window_wall_left' not in original.collection.children else None
    # 候选黑板为场景直接集合；另建浅拷贝集合，共享几何，只替换一处材质。
    source=bpy.data.collections['AST_chalkboard']
    other.collection.children.link(source)
    probe=next(o for o in other.objects if o.name==board.name)
    assert probe.active_material.as_pointer()==board.active_material.as_pointer()
    cam=original.camera.copy();cam.data=original.camera.data.copy();other.collection.objects.link(cam)
    cam.animation_data_clear();other.camera=cam
    cam.location.x+=.25
    assert abs(original.camera.location.x-cam.location.x)>.2
    assert other.world.as_pointer()!=original.world.as_pointer()
    common={'material_shared':probe.active_material.as_pointer()==board.active_material.as_pointer(),
      'camera_separate':other.camera.as_pointer()!=original.camera.as_pointer(),
      'world_separate':other.world.as_pointer()!=original.world.as_pointer()}
    other.collection.children.unlink(source)
    variant=source.copy();variant.name='TEST / board only variant';other.collection.children.link(variant)
    variant.objects.unlink(board)
    board_copy=board.copy();board_copy.data=board.data.copy()
    alt=material.copy();alt.name='TEST / board shot override';board_copy.data.materials.clear();board_copy.data.materials.append(alt)
    variant.objects.link(board_copy)
    assert board_copy.data.as_pointer()!=board.data.as_pointer()
    assert board_copy.active_material.as_pointer()!=material.as_pointer()
    assert board.active_material.as_pointer()==material.as_pointer()
    return {**common,'variant_material_separate':True,'shared_meshes_elsewhere':len(variant.objects)-1,
      'user_main_camera_unchanged':original.camera.name==data['before']['camera']}


before=data['before'];current=active_instances(scene)
expected={n:row for n,row in before['instances'].items() if row['collection']!='AST_chalkboard'}
assert current==expected
assert scene.frame_current==before['frame'] and [scene.frame_start,scene.frame_end]==before['range'] and scene.render.fps==before['fps']
assert sorted(a.name for a in bpy.data.actions if not a.library)==before['actions']
assert all(o.library is None for o in bpy.data.objects)
assert all(m.library is None for m in bpy.data.materials)
assert board.name in scene.objects and board.select_get()
controls=bpy.data.collections['LOOKDEV / material selectors']
target=bpy.data.objects['MAT / Blackboard / Aged baked green coating']
assert target.active_material.as_pointer()==material.as_pointer() and target.hide_render
original_missing=set()
for im in bpy.data.images:
    if im.source!='FILE' or im.packed_file or not im.filepath:continue
    resolved=Path(bpy.path.abspath(im.filepath,library=im.library))
    if not resolved.exists():original_missing.add(im.name)
# 图像依赖的未解析项属于原工程 Houdini opdef 路径；逐项在报告中披露。
node_test=check_material_target();scene_test=second_scene_probe()
summary={'passed':True,'scene':scene.name,'frame':scene.frame_current,'fps':scene.render.fps,
 'instance_count':len(current),'board_direct':board.name in scene.objects,
 'board_material_nodes':len(material.node_tree.nodes),'material_controls':len(controls.objects),
 'target_is_original_material':True,'node_test':node_test,'second_scene':scene_test,
 'libraries':[l.filepath for l in bpy.data.libraries if l.users>0],
 'unresolved_images':sorted(original_missing)}
report_name='published_validation.json' if Path(bpy.data.filepath).name=='drop_sq010_sh010_shot.blend' else 'validation.json'
(CACHE/report_name).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False))
