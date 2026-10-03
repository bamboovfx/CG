"""只读核对资产源与发布库的数据归属、场景挂载和文件大小；不保存 blend。"""
import bpy
import json
from pathlib import Path

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
reports = []

def collection_paths(root, target, trail):
    """输入集合树、目标和路径；返回目标在场景树中的所有路径。"""
    found = [trail + [root.name]] if root == target else []
    for child in root.children:
        found.extend(collection_paths(child, target, trail + [root.name]))
    return found

for relative in ['02_assets/work/classroom_props.blend', '02_assets/library/classroom_assets.blend']:
    path = ROOT / relative
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    # 记录所有场景的根集合，区分存在于数据块与可以在当前场景找到。
    scenes = [{'name': s.name, 'roots': [c.name for c in s.collection.children]} for s in bpy.data.scenes]
    board = bpy.data.collections.get('AST_chalkboard')
    mat = bpy.data.materials.get('Blackboard / Aged baked green coating')
    material_nodes = []
    if mat and mat.node_tree:
        for node in mat.node_tree.nodes:
            values = {}
            for socket in node.inputs:
                if not socket.is_linked and hasattr(socket, 'default_value'):
                    value = socket.default_value
                    values[socket.name] = list(value) if hasattr(value, '__len__') and not isinstance(value, str) else value
            material_nodes.append({'name': node.name, 'type': node.bl_idname, 'unlinked_inputs': values})
    targets = []
    for name in ['Unique wiped writing surface', 'Board steel writing substrate']:
        ob = bpy.data.objects.get(name)
        if ob:
            targets.append({'name': ob.name, 'library': ob.library.filepath if ob.library else None,
                            'collections': [c.name for c in ob.users_collection],
                            'materials': [{'name': m.name, 'library': m.library.filepath if m.library else None,
                                           'nodes': len(m.node_tree.nodes) if m.node_tree else 0}
                                          for m in ob.data.materials if m],
                            'vertices': len(ob.data.vertices), 'polygons': len(ob.data.polygons)})
    reports.append({'path': str(path), 'bytes': path.stat().st_size,
                    'libraries': [lib.filepath for lib in bpy.data.libraries],
                    'scenes': scenes, 'collections': len(bpy.data.collections),
                    'objects': len(bpy.data.objects), 'materials': len(bpy.data.materials),
                    'board': {'library': board.library.filepath if board and board.library else None,
                              'users': board.users if board else None,
                              'fake_user': board.use_fake_user if board else None,
                              'paths': {s.name: collection_paths(s.collection, board, []) for s in bpy.data.scenes},
                              'objects': len(board.all_objects) if board else None},
                    'board_objects': targets, 'board_material_nodes': material_nodes,
                    'unmounted_collections': [c.name for c in bpy.data.collections
                                             if not any(collection_paths(s.collection, c, []) for s in bpy.data.scenes)]})
out = ROOT / '07_pipeline/cache/pipeline_review_20260929/source_audit_readonly.json'
out.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(reports, ensure_ascii=False), flush=True)
