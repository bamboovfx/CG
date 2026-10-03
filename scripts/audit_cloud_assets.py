"""后台只读盘点场景依赖，区分打包资源和外部资源；不修改工作工程。"""
import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(path):
    """输入文件路径；分块返回 SHA256，避免把大工程一次读入内存。"""
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inspect_file(relative):
    """输入项目相对 blend 路径；返回重开后的资源、场景和完整性证据。"""
    path = ROOT / relative
    before = fingerprint(path)
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    resources = []
    for kind in ('libraries', 'images', 'fonts', 'sounds', 'movieclips', 'cache_files', 'volumes'):
        for block in getattr(bpy.data, kind):
            value = getattr(block, 'filepath', '')
            if not value or value == '<builtin>':
                continue
            packed = bool(getattr(block, 'packed_file', None) or getattr(block, 'packed_files', None))
            resolved = bpy.path.abspath(value, library=block.library)
            resources.append(dict(kind=kind, name=block.name, path=value, absolute=resolved,
                                  packed=packed, users=block.users, exists=Path(resolved).exists()))
    caches = []
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            cache = getattr(modifier, 'point_cache', None)
            if cache:
                caches.append(dict(object=obj.name, type=modifier.type, baked=cache.is_baked,
                                   disk=cache.use_disk_cache, external=cache.use_external,
                                   filepath=cache.filepath))
    row = dict(file=relative, sha256=before, unchanged=fingerprint(path) == before,
               bytes=path.stat().st_size, resources=resources, caches=caches,
               objects=len(bpy.data.objects), meshes=len(bpy.data.meshes),
               materials=len(bpy.data.materials), actions=len(bpy.data.actions),
               scenes=[dict(name=s.name, frames=[s.frame_start, s.frame_end], fps=s.render.fps,
                            camera=s.camera.name if s.camera else None) for s in bpy.data.scenes])
    print('AUDIT', relative, 'external', sum(not r['packed'] for r in resources),
          'missing', sum(not r['packed'] and not r['exists'] for r in resources), flush=True)
    return row


def main():
    """输入 JSON 检查任务路径；逐文件写证据，任何重开失败以非零退出。"""
    job = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text(encoding='utf-8-sig'))
    rows = []
    output = ROOT / job['output']
    output.parent.mkdir(parents=True, exist_ok=True)
    for relative in job['files']:
        rows.append(inspect_file(relative))
        output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
