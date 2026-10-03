"""仅规范上传工程的项目内资源路径；保存前后校验几何、材质、动画及场景。"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / '07_pipeline/scripts'))
from cleanup_wood_rear_stamp import geometry_digest
from replace_scene_chairs import action_state, scene_signature
from audit_cloud_assets import fingerprint


def content_signature():
    """无参数；返回排除路径表示的内容摘要，保护网格、材质节点、实例和镜头设置。"""
    data = {
        'meshes': {m.name: geometry_digest(m) for m in bpy.data.meshes},
        'objects': {o.name: dict(type=o.type, matrix=[list(r) for r in o.matrix_world],
                     parent=o.parent.name if o.parent else None,
                     instance=o.instance_collection.name if o.instance_collection else None,
                     materials=[s.material.name if s.material else None for s in o.material_slots],
                     properties=dict(o.items()), hidden=[o.hide_render, o.hide_viewport]) for o in bpy.data.objects},
        'collections': {c.name: dict(objects=sorted(o.name for o in c.objects),
                                    children=sorted(x.name for x in c.children)) for c in bpy.data.collections},
        'materials': {m.name: scene_signature(m.node_tree) for m in bpy.data.materials},
        'groups': {g.name: scene_signature(g) for g in bpy.data.node_groups if g.bl_idname == 'ShaderNodeTree'},
        'worlds': {w.name: scene_signature(w.node_tree) for w in bpy.data.worlds},
        'actions': action_state(),
        'scenes': {s.name: dict(frames=[s.frame_start, s.frame_end, s.frame_current], fps=s.render.fps,
                    camera=s.camera.name if s.camera else None, world=s.world.name if s.world else None,
                    resolution=[s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage],
                    engine=s.render.engine, samples=s.cycles.samples,
                    color=[s.view_settings.view_transform, s.view_settings.look, s.view_settings.exposure])
                   for s in bpy.data.scenes},
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True,
        default=lambda v: getattr(v, 'name', str(v))).encode()).hexdigest()


def main():
    """输入工程相对路径；仅改路径和磁盘压缩，重开内容不同则从临时副本回滚。"""
    relative = sys.argv[sys.argv.index('--') + 1]
    source = ROOT / relative
    backup = ROOT / '.local/portability-backup' / source.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    original_hash = fingerprint(source)
    shutil.copy2(source, backup)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    before = content_signature()
    changes = []
    for kind in ('libraries', 'images', 'fonts', 'sounds', 'movieclips', 'cache_files', 'volumes'):
        for block in getattr(bpy.data, kind):
            value = getattr(block, 'filepath', '')
            if not value or value == '<builtin>' or block.library:
                continue
            # 打包资源从工程内读取；改其来源标签会触发 Blender 自动重打包，故保留原标签。
            if getattr(block, 'packed_file', None) or getattr(block, 'packed_files', None):
                continue
            absolute = Path(bpy.path.abspath(value)).resolve()
            try:
                absolute.relative_to(ROOT)
            except ValueError:
                continue
            portable = '//' + os.path.relpath(absolute, source.parent).replace('\\', '/')
            if value != portable:
                changes.append(dict(kind=kind, name=block.name, before=value, after=portable))
                block.filepath = portable
    assert content_signature() == before, '路径规范化改变了实际资源解析或场景内容'
    assert fingerprint(source) == original_hash, '检查期间用户重新保存，停止覆盖'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(source), check_existing=False, relative_remap=False, compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    after = content_signature()
    if after != before:
        shutil.copy2(backup, source)
        raise RuntimeError('保存重开后内容不一致，已恢复原文件')
    result = dict(file=relative, before_sha256=original_hash, after_sha256=fingerprint(source),
                  semantic_before=before, semantic_after=after, content_preserved=True,
                  changes=changes, bytes=source.stat().st_size)
    destination = ROOT / '06_review/cloud_assets_20261003' / (source.stem + '_portable.json')
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PORTABLE', relative, 'paths', len(changes), 'bytes', source.stat().st_size, flush=True)


if __name__ == '__main__':
    main()
