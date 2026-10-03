"""清除实时木椅工程中的印记分支；先备份未保存编辑，再原位保存与审计。"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '06_review/wood_stamp_cleanup_20261001'
BACKUP = ROOT / '07_pipeline/cache/wood_stamp_cleanup_20261001/before_cleanup.blend'
CURRENT = ROOT / '02_assets/work/school_chair.blend'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tripo_wood_appearance_blender import process_signature


def geometry_digest(mesh):
    """输入网格，返回全部几何、法线、UV与材质分配摘要，排除待删印记属性。"""
    digest = hashlib.sha256()
    for collection, prop, size, dtype in [
        (mesh.vertices, 'co', 3, np.float32),
        (mesh.loops, 'vertex_index', 1, np.int32),
        (mesh.polygons, 'loop_start', 1, np.int32),
        (mesh.polygons, 'loop_total', 1, np.int32),
        (mesh.polygons, 'material_index', 1, np.int32),
        (mesh.corner_normals, 'vector', 3, np.float32),
    ]:
        values = np.empty(len(collection) * size, dtype=dtype)
        collection.foreach_get(prop, values)
        digest.update(values.tobytes())
    for uv in mesh.uv_layers:
        values = np.empty(len(uv.data) * 2, dtype=np.float32)
        uv.data.foreach_get('uv', values)
        digest.update(uv.name.encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def protected_state():
    """读取当前场景，返回木板、受保护材质、对象位置与编辑状态摘要。"""
    data = {'geometry': {}, 'materials': {}, 'objects': {}, 'context': {}}
    for name in ['LP_part_02', 'LP_part_09']:
        ob = bpy.data.objects[name]
        data['geometry'][name] = geometry_digest(ob.data)
        for n in ob.data.materials[0].node_tree.nodes:
            if n.get('wood_layers_role') in {'process', 'surface_dirt'}:
                data['materials'][name + '/' + n.get('wood_layers_role')] = process_signature(n.node_tree)
        data['materials'][name + '/side'] = process_signature(ob.data.materials[1].node_tree)
    for ob in bpy.data.objects:
        data['objects'][ob.name] = [list(row) for row in ob.matrix_world]
    sc = bpy.context.scene
    data['context'] = {'active': bpy.context.view_layer.objects.active.name,
        'selected': sorted(o.name for o in bpy.context.selected_objects), 'mode': bpy.context.mode,
        'camera': sc.camera.name, 'frame': sc.frame_current, 'world': sc.world.name,
        'world_graph': process_signature(sc.world.node_tree),
        'resolution': [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
        'render_path': sc.render.filepath, 'samples': sc.cycles.samples}
    return data


def branch_nodes(group):
    """输入表现组，返回仅印记使用的节点集合；保留共享Age、颜色和用户排版。"""
    mixes = [n for n in group.nodes if n.get('wood_layers_role') == 'rear_stamp_preserved']
    assert len(mixes) == 1, group.name
    mix = mixes[0]
    assert not mix.inputs[0].is_linked and mix.inputs[0].default_value == 0
    assert mix.blend_type == 'MIX' and not mix.use_clamp
    remove = {n for n in group.nodes if n.get('wood_layers_role') in
        {'rear_stamp', 'rear_stamp_preserved', 'stamp_note'}}
    frontier = [n for n in remove if n.type == 'TEX_IMAGE']
    frontier += [l.to_node for l in group.links
        if l.from_node.type == 'GROUP_INPUT' and l.from_socket.name == 'Rear']
    # 向前只追踪印记运算，不跨过颜色混合进入最终材质。
    while frontier:
        n = frontier.pop()
        if n.type not in {'TEX_IMAGE', 'MATH', 'REROUTE'}:
            raise RuntimeError('印记支路包含未预期节点：' + n.name)
        remove.add(n)
        for l in group.links:
            if l.from_node == n and l.to_node not in remove:
                if l.to_node == mix:
                    continue
                frontier.append(l.to_node)
    # 补齐仅服务印记的Age倍率及孤立转接点，不清理其它无关闲置节点。
    changed = True
    while changed:
        changed = False
        for n in group.nodes:
            if n in remove or n.type not in {'MATH', 'REROUTE'}:
                continue
            outgoing = [l for l in group.links if l.from_node == n]
            if outgoing and all(l.to_node in remove for l in outgoing):
                remove.add(n)
                changed = True
    return mix, remove


def clear_group(group, mix, remove):
    """输入预检过的印记支路，返回删除清单；把原颜色链直接接回原输出。"""
    base = list(mix.inputs[1].links)
    assert len(base) == 1
    targets = [l.to_socket for l in mix.outputs[0].links]
    for target in targets:
        group.links.new(base[0].from_socket, target)
    removed = sorted(n.name for n in remove)
    for n in list(remove):
        group.nodes.remove(n)
    for item in list(group.interface.items_tree):
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == 'Rear':
            group.interface.remove(item)
    if 'legacy_stamp_disabled' in group:
        del group['legacy_stamp_disabled']
    return removed


def main():
    """读取当前实时工程，备份、定向清理、验证保护项并保存原文件，返回审计。"""
    assert Path(bpy.data.filepath).resolve() == CURRENT.resolve()
    assert bpy.context.mode == 'OBJECT'
    groups = [bpy.data.node_groups['Wood / 表现层 / Scanned finish ' + board]
        for board in ['seat', 'back']]
    plans = [(g, *branch_nodes(g)) for g in groups]
    before = protected_state()
    dirty = bpy.data.is_dirty
    OUT.mkdir(parents=True, exist_ok=True)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    assert not BACKUP.exists(), '恢复副本已存在；先检查历史执行状态'
    bpy.ops.wm.save_as_mainfile(filepath=str(BACKUP), copy=True)
    assert Path(bpy.data.filepath).resolve() == CURRENT.resolve()
    audit = {'source_had_unsaved_edits': dirty, 'backup': str(BACKUP),
        'current': str(CURRENT), 'groups': {}, 'attributes': [], 'images': [], 'root_nodes': []}
    for g, mix, remove in plans:
        audit['groups'][g.name] = clear_group(g, mix, remove)
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for n in list(mat.node_tree.nodes):
            if n.type == 'ATTRIBUTE' and n.attribute_name == 'reference_rear':
                audit['root_nodes'].append(mat.name + '/' + n.name)
                mat.node_tree.nodes.remove(n)
            elif n.type == 'FRAME' and '背面印记限位' in n.label:
                n.label = n.label.replace('三个独立强度，背面印记限位', '划痕／老化／磨损独立强度')
    for mesh in bpy.data.meshes:
        attr = mesh.attributes.get('reference_rear')
        if attr:
            audit['attributes'].append(mesh.name)
            mesh.attributes.remove(attr)
    for image in list(bpy.data.images):
        if image.name.split('.')[0] == 'StampMask':
            # 图像编辑器也会计入users；确认无材质/数据块引用后解除该UI引用。
            assert not bpy.data.user_map(subset={image}).get(image), image.name
            audit['images'].append(image.name)
            bpy.data.images.remove(image)
    assert before == protected_state(), '几何／工艺／脏渍／侧边／场景保护项发生变化'
    assert all(not mesh.attributes.get('reference_rear') for mesh in bpy.data.meshes)
    assert all(not any(s.name == 'Rear' for s in g.interface.items_tree) for g in groups)
    assert not any('StampMask' in im.name for im in bpy.data.images)
    audit['protected_state'] = before
    audit['protected_state_unchanged'] = True
    save_result = bpy.ops.wm.save_as_mainfile(filepath=str(CURRENT))
    audit['saved'] = 'FINISHED' in save_result
    (OUT / 'validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit


if __name__ == '__main__':
    print(json.dumps(main(), ensure_ascii=False), flush=True)
