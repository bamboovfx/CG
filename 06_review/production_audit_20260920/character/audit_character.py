"""只读检查角色与邻近桌椅；输出 JSON，不保存或改写 Blender 文件。"""
import bpy
import json
from pathlib import Path
from mathutils import Vector, Matrix

OUT = Path(__file__).resolve().parent


def serial(value):
    """输入 Blender 自定义属性值；返回可写入 JSON 的普通类型。"""
    if hasattr(value, 'to_list'):
        return value.to_list()
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def box_from_points(points):
    """输入世界空间顶点列表；返回轴对齐最小、最大坐标。"""
    if not points:
        return None
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def collection_points(collection, matrix=Matrix.Identity(4), level=0):
    """输入实例集合及变换；返回原始对象包围盒顶点，包含集合偏移，非精确碰撞形体。"""
    if level > 4:
        return []
    points = []
    base = matrix @ Matrix.Translation(-collection.instance_offset)
    for item in collection.all_objects:
        transform = base @ item.matrix_world
        if item.instance_collection:
            points.extend(collection_points(item.instance_collection, transform, level + 1))
        elif item.type in {'MESH', 'CURVE', 'FONT'}:
            points.extend(transform @ Vector(v) for v in item.bound_box)
    return points


def object_record(obj):
    """输入场景对象；返回位置、父子、动画、动力学及可追踪属性。"""
    record = {'name': obj.name, 'type': obj.type,
              'location': list(obj.location), 'world_location': list(obj.matrix_world.translation),
              'rotation_euler': list(obj.rotation_euler), 'scale': list(obj.scale),
              'matrix_world': [list(row) for row in obj.matrix_world],
              'parent': obj.parent.name if obj.parent else None,
              'children': [o.name for o in obj.children],
              'constraints': [c.type for c in obj.constraints],
              'modifiers': [m.type for m in obj.modifiers],
              'rigid_body': bool(obj.rigid_body),
              'animation_data': bool(obj.animation_data),
              'custom_properties': {k: serial(obj[k]) for k in obj.keys()},
              'instance_collection': obj.instance_collection.name if obj.instance_collection else None,
              'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport,
              'library': obj.library.filepath if obj.library else None}
    if obj.instance_collection:
        record['bounds_raw'] = box_from_points(collection_points(obj.instance_collection, obj.matrix_world))
    return record


scene = bpy.context.scene
figure = bpy.data.collections.get('chr_tin_figure')
figures = [object_record(o) for o in figure.all_objects] if figure else []
nearby = [object_record(o) for o in scene.objects
          if o.name.startswith('asset_desk_set_') and o.location.x < -.8 and -4 < o.location.y < 0]
collections = sorted({o.instance_collection for o in figure.all_objects if o.instance_collection}, key=lambda c: c.name)
result = {'source': bpy.data.filepath, 'scene': scene.name,
          'frame': scene.frame_current, 'frame_range': [scene.frame_start, scene.frame_end],
          'fps': scene.render.fps, 'fps_base': scene.render.fps_base,
          'actions': [a.name for a in bpy.data.actions],
          'armatures': [o.name for o in scene.objects if o.type == 'ARMATURE'],
          'figure_collection_properties': {k: serial(figure[k]) for k in figure.keys()},
          'figures': figures, 'nearby_desk_chair': nearby,
          'instance_assets': [{'name': c.name, 'offset': list(c.instance_offset),
                               'objects': len(c.all_objects),
                               'library': c.library.filepath if c.library else None,
                               'raw_bounds': box_from_points(collection_points(c))} for c in collections],
          'cameras': [object_record(o) for o in scene.objects if o.type == 'CAMERA'],
          'warning': 'AABB bounds use unmodified mesh bounds; overlap does not prove mesh intersection.'}
for kind in ['chair', 'desk']:
    instance = scene.objects.get('asset_desk_set_06_' + kind)
    if not instance:
        continue
    base = instance.matrix_world @ Matrix.Translation(-instance.instance_collection.instance_offset)
    result['hero_' + kind + '_parts'] = [
        {'name': o.name, 'type': o.type,
         'bounds': box_from_points([base @ o.matrix_world @ Vector(v) for v in o.bound_box])}
        for o in instance.instance_collection.all_objects if o.type in {'MESH', 'CURVE', 'FONT'}]
(OUT / 'character_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('CHARACTER_AUDIT_COMPLETE', len(figures), [c.name for c in collections], flush=True)
