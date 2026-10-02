"""只读核查清理前后的正式工程与当前候选依赖；不保存或修改任何 blend。

用法：Blender --background --factory-startup --python 本脚本 -- before|after。
输出：06_review/cleanup_20260927/dependencies_<阶段>.json。
"""
import bpy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend',
    '03_shots/sq010/sh010/work/drop_sq010_sh010_layout.blend',
    '02_assets/work/classroom_environment.blend',
    '02_assets/work/classroom_props.blend',
    '02_assets/library/classroom_assets.blend',
    '02_assets/work/classroom_curtain_simulation.blend',
    '02_assets/materials/school_desk/desk_material_lookdev.blend',
    '07_pipeline/cache/sh010_blocking_20260920/pose_fit_candidate.blend',
]


def inspect_open_file():
    """输入当前已打开场景；返回全部外部路径、模拟缓存和场景摘要。"""
    paths = sorted({str(Path(p).resolve()) for p in bpy.utils.blend_paths(absolute=True, packed=False) if p})
    # blend_paths 也包含内嵌 Text 的历史来源；真实外部资源另外分类。
    resources = set()
    for library in bpy.data.libraries:
        resources.add(str(Path(bpy.path.abspath(library.filepath, library=library.parent)).resolve()))
    for collection in (bpy.data.images, bpy.data.fonts, bpy.data.sounds,
                       bpy.data.movieclips, bpy.data.cache_files, bpy.data.volumes):
        for block in collection:
            value = getattr(block, 'filepath', '')
            packed = bool(getattr(block, 'packed_file', None)) or bool(getattr(block, 'packed_files', None))
            if value and value != '<builtin>' and not packed:
                resources.add(str(Path(bpy.path.abspath(value, library=block.library)).resolve()))
    caches = []
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            cache = getattr(modifier, 'point_cache', None)
            if cache:
                caches.append({'object': obj.name, 'type': modifier.type,
                               'baked': cache.is_baked, 'disk': cache.use_disk_cache,
                               'external': cache.use_external, 'filepath': cache.filepath,
                               'start': cache.frame_start, 'end': cache.frame_end})
                if cache.use_external and cache.filepath:
                    paths.append(str(Path(bpy.path.abspath(cache.filepath, library=obj.library)).resolve()))
    return {'file': bpy.data.filepath, 'dependencies': sorted(set(paths)),
            'resource_dependencies': sorted(resources),
            'missing_resources': sorted(p for p in resources if not Path(p).exists()),
            'embedded_text_origins': [t.filepath for t in bpy.data.texts if t.filepath],
            'missing': [p for p in paths if not Path(p).exists()],
            'caches': caches, 'objects': len(bpy.data.objects),
            'actions': len(bpy.data.actions),
            'frame_range': [bpy.context.scene.frame_start, bpy.context.scene.frame_end],
            'fps': bpy.context.scene.render.fps}


def main():
    """读取固定保护名单，保存检查证据；文件重开失败直接停止，不执行清理。"""
    phase = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'before'
    assert phase in {'before', 'after'}
    rows = []
    for relative in SOURCES:
        path = ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
        row = inspect_open_file()
        row['sha256'] = digest
        row['unchanged'] = hashlib.sha256(path.read_bytes()).hexdigest() == digest
        rows.append(row)
        print('AUDIT', relative, 'resources', len(row['resource_dependencies']),
              'missing_resources', len(row['missing_resources']),
              'historical_path_metadata_missing', len(row['missing']), flush=True)
    out = ROOT / '06_review/cleanup_20260927'
    out.mkdir(parents=True, exist_ok=True)
    (out / f'dependencies_{phase}.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
