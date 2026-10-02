"""为已审核的单扇推拉窗建立 Empty 控制器，并检查绑定与滑动后的世界变换。

输入：部件清单及当前建筑源。输出：候选工程、绑定验证报告；不修改网格或材质。
可通过 apply_controller() 在已经确认身份的 Blender MCP 实例中复用。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def matrix_error(a, b):
    """输入两个4×4矩阵，返回最大元素误差，用于检查绑定前后的世界位置。"""
    return max(abs(a[r][c] - b[r][c]) for r in range(4) for c in range(4))


def apply_controller(manifest):
    """输入已审核部件清单，返回控制器与位置检查结果；保留原有部件世界变换。"""
    collection = bpy.data.collections[manifest['collection']]
    parts = [bpy.data.objects[name] for name in manifest['parts']]
    assert all(o in list(collection.objects) for o in parts)
    assert all(o.parent is None and o.animation_data is None for o in parts)
    assert manifest['controller'] not in bpy.data.objects
    before = {o.name: o.matrix_world.copy() for o in bpy.context.scene.objects}
    before_data = {o.name: (o.data, tuple(o.users_collection)) for o in parts}
    anchor = bpy.data.objects[manifest['pane']].matrix_world.translation.copy()

    # 原点显示在玻璃中心，Delta Location 保留安装位置；Location Y=0 表示绑定时的位置。
    control = bpy.data.objects.new(manifest['controller'], None)
    collection.objects.link(control)
    control.empty_display_type = 'PLAIN_AXES'
    control.empty_display_size = 0.24
    control.show_in_front = True
    control.show_name = True
    control.delta_location = anchor
    control.lock_location = (True, False, True)
    control.lock_rotation = (True, True, True)
    control.lock_scale = (True, True, True)
    control['window_controller_role'] = 'left exterior lower sliding sash'
    control['source_pane'] = manifest['pane']
    control['operation'] = 'G Y: slide on track; Location Y=0: original position'
    control['controlled_parts'] = json.dumps(manifest['parts'], ensure_ascii=False)
    bpy.context.view_layer.update()

    # 显式保留父级逆矩阵和原有局部矩阵，避免零件绑定时跳动。
    inverse = control.matrix_world.inverted()
    for obj in parts:
        obj.parent = control
        obj.matrix_parent_inverse = inverse
        obj.matrix_world = before[obj.name]
    bpy.context.view_layer.update()
    bind_error = max(matrix_error(o.matrix_world, before[o.name]) for o in parts)
    assert bind_error < 0.00001, bind_error

    # 在候选/实际内存中试滑30cm，检查只有这扇窗移动；验证后立即恢复。
    try:
        control.location.y = -0.30
        bpy.context.view_layer.update()
        translation = Matrix.Translation(Vector((0, -0.30, 0)))
        slide_error = max(matrix_error(o.matrix_world, translation @ before[o.name]) for o in parts)
        unchanged_error = max(
            (matrix_error(o.matrix_world, before[o.name]) for o in bpy.context.scene.objects
             if o.name in before and o not in parts), default=0)
        assert slide_error < 0.00001, slide_error
        assert unchanged_error < 0.00001, unchanged_error
    finally:
        control.location.y = 0
        bpy.context.view_layer.update()
    restored_error = max(matrix_error(o.matrix_world, before[o.name]) for o in parts)
    assert restored_error < 0.00001, restored_error
    assert all((o.data, tuple(o.users_collection)) == before_data[o.name] for o in parts)

    # 选中控制器，便于用户在当前建筑源直接按 G Y 操作。
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)
    control.select_set(True)
    bpy.context.view_layer.objects.active = control
    return {'controller': control.name, 'pane': manifest['pane'], 'part_count': len(parts),
            'parts': manifest['parts'], 'bind_world_error': bind_error,
            'slide_30cm_error': slide_error, 'other_objects_world_error': unchanged_error,
            'restored_world_error': restored_error, 'location': list(control.location),
            'delta_location': list(control.delta_location)}


def main():
    """读取命令行的候选输出路径并执行绑定；只保存到显式指定的候选路径。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    source = Path(bpy.data.filepath)
    assert source.resolve() != Path(args.output).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['source_sha256']
    result = apply_controller(manifest)
    bpy.ops.wm.save_as_mainfile(filepath=args.output, check_existing=False, relative_remap=True)
    result['candidate'] = args.output
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('WINDOW_CONTROLLER_CANDIDATE_OK', flush=True)


if __name__ == '__main__':
    main()
