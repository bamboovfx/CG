"""沿现有16边交界分离三个胶脚，保留每面坐标、UV与自定义法线，复用现有材质。"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cleanup_wood_rear_stamp import geometry_digest
from tripo_wood_appearance_blender import process_signature
from wood_layers_blender import aim

WORK = ROOT / '07_pipeline/cache/chair_foot_caps_20261001'
OUT = ROOT / '06_review/chair_foot_caps_20261001'
REGIONS = [('LP_part_01', 'rear', 'Foot cap / rear left'),
           ('LP_part_13', 'front', 'Foot cap / front right'),
           ('LP_part_13', 'rear', 'Foot cap / rear right')]
ID = 'foot_split_source_face'


def face_records(mesh):
    """输入带临时源面编号的网格，返回每面的角点坐标／UV／法线用于分离前后对比。"""
    rows = {}
    normals = mesh.corner_normals
    for face in mesh.polygons:
        key = mesh.attributes[ID].data[face.index].value
        values = []
        for li in face.loop_indices:
            values += list(mesh.vertices[mesh.loops[li].vertex_index].co)
            for uv in mesh.uv_layers:
                values += list(uv.data[li].uv)
            values += list(normals[li].vector)
        rows[key] = np.asarray(values, dtype=np.float32)
    return rows


def state():
    """读取非目标几何、原有材质组及场景变换，返回保护摘要。"""
    return {'geometry': {o.name: geometry_digest(o.data) for o in bpy.data.objects
                        if o.type == 'MESH' and o.name not in ['LP_part_01', 'LP_part_13']
                        and not o.get('foot_cap_separated')},
            'materials': {m.name: process_signature(m.node_tree) for m in bpy.data.materials if m.use_nodes
                          and not m.get('foot_cap_material')},
            'groups': {g.name: process_signature(g) for g in bpy.data.node_groups},
            'transforms': {o.name: [list(row) for row in o.matrix_world] for o in bpy.data.objects
                           if not o.get('foot_cap_separated')}}


def split():
    """输入当前椅子，输出胶脚分件／形状UV法线对比；只拆已有面，不切面或补造形状。"""
    assert bpy.context.mode == 'OBJECT'
    assert not any(bpy.data.objects.get(name) for _, _, name in REGIONS), '胶脚已分件'
    before = state()
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    select_mode = bpy.context.tool_settings.mesh_select_mode[:]
    original = {}
    for name in ['LP_part_01', 'LP_part_13']:
        mesh = bpy.data.objects[name].data
        assert ID not in mesh.attributes
        attr = mesh.attributes.new(ID, 'INT', 'FACE')
        for index, entry in enumerate(attr.data):
            entry.value = index
        original[name] = face_records(mesh)
    caps = []
    for source, side, name in REGIONS:
        ob = bpy.data.objects[source]
        # 只选现有胶脚面：高度低于12mm，前后由Y判定；长钢管面不会被选中。
        for other in bpy.context.selected_objects:
            other.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        for v in ob.data.vertices:
            v.select = False
        for e in ob.data.edges:
            e.select = False
        for p in ob.data.polygons:
            points = [ob.matrix_world @ ob.data.vertices[i].co for i in p.vertices]
            p.select = all(v.z < .012 for v in points) and ((sum(v.y for v in points) < 0) == (side == 'front'))
        count = sum(p.select for p in ob.data.polygons)
        assert 450 < count < 650, (source, side, count)
        known = set(bpy.data.objects)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        created = set(bpy.data.objects) - known
        assert len(created) == 1
        cap = created.pop()
        cap.name = name
        cap['foot_cap_separated'] = True
        cap['foot_cap_source'] = source
        caps.append(cap)
    # 比对源面并集，防止丢面、重复面、UV重排或分离后法线重算。
    errors = {}
    for source, old in original.items():
        objects = [bpy.data.objects[source]] + [o for o in caps if o['foot_cap_source'] == source]
        found = {}
        for ob in objects:
            # 分离改变角点法线的编码基底，显式转移原向量以免边界反光变化。
            stride = 3 + 2 * len(ob.data.uv_layers) + 3
            normals = np.zeros((len(ob.data.loops), 3), dtype=np.float32)
            for face in ob.data.polygons:
                key = ob.data.attributes[ID].data[face.index].value
                old_corners = old[key].reshape((-1, stride))
                normals[list(face.loop_indices)] = old_corners[:, -3:]
            ob.data.normals_split_custom_set(normals.tolist())
            data = face_records(ob.data)
            assert not set(found).intersection(data), '源面重复'
            found.update(data)
        assert set(found) == set(old), '源面缺失'
        differences = [np.abs(found[k].reshape((-1, stride))-old[k].reshape((-1, stride))) for k in old]
        geo_uv_error = max(float(d[:, :-3].max()) for d in differences)
        normal_error = max(float(d[:, -3:].max()) for d in differences)
        angles = []
        for key in old:
            a = old[key].reshape((-1, stride))[:, -3:].astype(np.float64)
            b = found[key].reshape((-1, stride))[:, -3:].astype(np.float64)
            angles.extend(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=1),
                                                np.sum(a*b, axis=1))))
        angle_error = float(max(angles))
        assert geo_uv_error == 0, ('坐标UV发生变化', source, geo_uv_error)
        # Blender以16位相对基底编码自定义法线；检查真实夹角而非要求浮点逐位相同。
        assert angle_error < .05, ('法线转移误差过大', source, angle_error)
        errors[source] = {'source_faces': len(old), 'max_geometry_uv_error': geo_uv_error,
                          'max_normal_component_error': normal_error,
                          'max_normal_angle_degrees': angle_error,
                          'uv_layers': [u.name for u in bpy.data.objects[source].data.uv_layers]}
        for ob in objects:
            ob.data.attributes.remove(ob.data.attributes[ID])
    # 四个胶脚集中到同一子集合；三个新增件各复制原材质根树，便于独立调色。
    existing = bpy.data.objects['LP_part_00']
    parent = existing.users_collection[0]
    collection = bpy.data.collections.new('CHAIR / Foot caps')
    parent.children.link(collection)
    rubber = existing.active_material
    for cap in [existing] + caps:
        previous = list(cap.users_collection)
        collection.objects.link(cap)
        for old_collection in previous:
            old_collection.objects.unlink(cap)
        if cap != existing:
            mat = rubber.copy()
            mat.name = 'Chair foot caps / ' + cap.name.split('/ ')[-1]
            mat['foot_cap_material'] = True
            cap.data.materials.clear()
            cap.data.materials.append(mat)
            for p in cap.data.polygons:
                p.material_index = 0
    for ob in bpy.context.selected_objects:
        ob.select_set(False)
    for ob in selected:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.context.tool_settings.mesh_select_mode = select_mode
    bpy.context.view_layer.update()
    assert state() == before, '受保护对象／材质／场景变换被更改'
    return {'caps': [o.name for o in collection.objects], 'collection': collection.name,
            'sources': errors, 'protected_unchanged': True,
            'cap_faces': {o.name: len(o.data.polygons) for o in collection.objects},
            'materials': {o.name: o.active_material.name for o in collection.objects}}


def candidate():
    """从含用户编辑的备份拆件，保存候选并渲染底部近景；恢复相机和渲染设置。"""
    OUT.mkdir(parents=True, exist_ok=True)
    audit = json.loads((OUT/'candidate.json').read_text(encoding='utf-8')) if '--render-only' in sys.argv else split()
    (OUT/'candidate.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    sc = bpy.context.scene
    cam = sc.camera
    snapshot = (cam.location.copy(), cam.rotation_euler.copy(), cam.data.lens,
                sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage,
                sc.render.filepath, sc.cycles.samples, sc.cycles.seed, sc.cycles.device,
                sc.render.image_settings.color_depth)
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = 64
    sc.cycles.seed = 101
    sc.render.image_settings.color_depth = '8'
    cam.location = (.85, -1.12, .39)
    aim(cam, (0, -.025, .06))
    cam.data.lens = 70
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 880
    sc.render.resolution_percentage = 100
    sc.render.filepath = str(OUT/'feet.png')
    bpy.ops.render.render(write_still=True)
    (cam.location, cam.rotation_euler, cam.data.lens,
     sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage,
     sc.render.filepath, sc.cycles.samples, sc.cycles.seed, sc.cycles.device,
     sc.render.image_settings.color_depth) = snapshot
    if '--render-only' not in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'foot_caps_candidate.blend'))
    print('FOOT_CAPS_CANDIDATE ' + json.dumps(audit), flush=True)


if __name__ == '__main__':
    candidate()
