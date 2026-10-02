"""只读检查已打开的镜头；输出可核对的制作基线，可选渲染当前主机位，不保存 .blend。"""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '06_review/production_audit_20260920'


def fingerprint(path):
    """输入现存文件路径，返回尺寸、修改时间和内容哈希，供发现检查期间的外部修改。"""
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'mtime_ns': path.stat().st_mtime_ns, 'sha256': digest}


def animation_summary(block):
    """输入 Blender 数据块，返回动作、驱动和 NLA 概况；不据此推断表演已完成。"""
    ad = getattr(block, 'animation_data', None)
    if not ad:
        return None
    return {'name': block.name, 'type': type(block).__name__,
            'action': ad.action.name if ad.action else None,
            'drivers': len(ad.drivers), 'nla_tracks': len(ad.nla_tracks)}


def main():
    """读取当前场景并写审计 JSON；--render 仅在后台内存改变出图参数。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    OUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    source = Path(bpy.data.filepath)
    before = fingerprint(source)
    libraries = [{'path': bpy.path.abspath(lib.filepath), 'name': lib.name}
                 for lib in bpy.data.libraries]
    missing_images = [{'name': im.name, 'path': bpy.path.abspath(im.filepath, library=im.library)}
                      for im in bpy.data.images if im.source == 'FILE' and im.filepath
                      and not im.packed_file
                      and not Path(bpy.path.abspath(im.filepath, library=im.library)).is_file()]
    animated = [summary for block in list(bpy.data.objects) + list(bpy.data.cameras)
                if (summary := animation_summary(block))]
    world_nodes = []
    if scene.world and scene.world.node_tree:
        for node in scene.world.node_tree.nodes:
            row = {'type': node.bl_idname, 'name': node.name}
            for key in ('sun_elevation', 'sun_rotation', 'sun_disc', 'sky_type'):
                if hasattr(node, key):
                    row[key] = getattr(node, key)
            world_nodes.append(row)
    camera = scene.camera
    report = {'checked_at': datetime.now().astimezone().isoformat(),
              'read_only_blend': True, 'blender': bpy.app.version_string,
              'source': str(source), 'source_fingerprint': before,
              'scene': scene.name, 'frame': scene.frame_current,
              'frame_range': [scene.frame_start, scene.frame_end],
              'fps': scene.render.fps / scene.render.fps_base,
              'camera': {'name': camera.name, 'lens': camera.data.lens,
                         'matrix_world': [list(row) for row in camera.matrix_world]} if camera else None,
              'render': {'engine': scene.render.engine,
                         'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                         'percentage': scene.render.resolution_percentage,
                         'samples': scene.cycles.samples},
              'color_management': {key: getattr(scene.view_settings, key, None)
                                   for key in ('view_transform', 'look', 'exposure', 'gamma',
                                               'use_white_balance', 'white_balance_temperature', 'white_balance_tint')},
              'libraries': libraries, 'missing_images': missing_images,
              'local_objects': len([ob for ob in bpy.data.objects if not ob.library]),
              'local_lights': [ob.name for ob in scene.objects if ob.type == 'LIGHT' and not ob.library],
              'animated_objects_and_cameras': animated,
              'actions': [{'name': ac.name, 'frame_range': list(ac.frame_range), 'users': ac.users}
                          for ac in bpy.data.actions],
              'rigid_body_world': bool(scene.rigidbody_world),
              'world_nodes': world_nodes,
              'source_hash_unchanged_after_probe': fingerprint(source) == before}
    (OUT / 'scene_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('AUDIT_SUMMARY', json.dumps(report, ensure_ascii=False), flush=True)
    if args.render:
        assert camera and camera.name == 'cam_sh010_main', '主相机已变，停止自动评审。'
        assert not missing_images, '缺失贴图，先解决依赖。'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type != 'CPU'
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 32
        scene.cycles.use_denoising = True
        scene.render.resolution_x, scene.render.resolution_y = 1920, 810
        scene.render.resolution_percentage = 100
        scene.render.use_border = False
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.filepath = str(OUT / 'current_main.png')
        bpy.ops.render.render(write_still=True)
        assert fingerprint(source) == before, '检查过程中工作文件被其他程序修改。'
        print('BASELINE_RENDER_OK', flush=True)


if __name__ == '__main__':
    main()
