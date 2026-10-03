"""只读检查最新正式镜头，避免把上轮候选覆盖用户之后的保存。"""
import bpy,json,hashlib
from pathlib import Path
from collections import Counter
root=Path('D:/00_projects/10_CG/Shot_Test')
shot=Path(bpy.data.filepath)
board=bpy.data.collections.get('AST_chalkboard')
scene=bpy.context.scene
inst=next((o for o in scene.objects if o.instance_collection==board),None)
data={'source':str(shot),'sha256':hashlib.sha256(shot.read_bytes()).hexdigest(),
 'frame':scene.frame_current,'range':[scene.frame_start,scene.frame_end],'fps':scene.render.fps,
 'objects':len(scene.objects),'library_paths':[bpy.path.abspath(l.filepath) for l in bpy.data.libraries],
 'instance_count':dict(Counter(o.instance_collection.name for o in scene.objects if o.instance_collection)),
 'board':{'objects':len(board.all_objects),'instance':inst.name if inst else None,
   'instance_matrix':[list(row) for row in inst.matrix_world] if inst else None,
   'collection_offset':list(board.instance_offset),
   'multiple_users':[o.name for o in board.all_objects if len(o.users_collection)!=1][:10],
   'material':bpy.data.objects['Unique wiped writing surface'].active_material.name,
   'material_nodes':len(bpy.data.objects['Unique wiped writing surface'].active_material.node_tree.nodes)},
 'actions':[a.name for a in bpy.data.actions if not a.library]}
out=root/'07_pipeline/cache/pipeline_review_20260929/latest_audit.json'
out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(data,ensure_ascii=False))
