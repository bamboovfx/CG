"""生成受依赖保护的迁移和清理清单；本脚本只规划，不执行删除。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / '06_review/cloud_assets_20261003'


def main():
    """输入只读场景审计和文件清单；输出保留迁移、逐文件删除计划及统计。"""
    rows = json.loads((REVIEW / 'dependencies_before.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / '.local/precloud_inventory.json').read_text(encoding='utf-8-sig'))
    assert len(rows) == 11 and all(row['unchanged'] for row in rows)
    moves = {
        '07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend':
            '02_assets/work/school_chair.blend',
        '07_pipeline/cache/classroom_props_refresh_20261001/approved_material_library.blend':
            '02_assets/work/approved_material_library.blend',
        '07_pipeline/cache/classroom_props_refresh_20261001/school_desk_v4_parts.blend':
            '02_assets/work/school_desk_parts.blend',
        '07_pipeline/cache/classroom_props_refresh_20261001/school_desk_v4_raw.fbx':
            '02_assets/authoring/school_desk/school_desk_raw.fbx',
        '07_pipeline/cache/tripo_chair_multiview_20260929/tripo_chair_multiview_p2_20260929_autosave_0.spp':
            '02_assets/authoring/school_chair/school_chair.spp',
        '07_pipeline/cache/tripo_chair_multiview_20260929/tripo_chair_painter_input.fbx':
            '02_assets/authoring/school_chair/painter_input.fbx',
        '07_pipeline/cache/tripo_chair_multiview_20260929/tripo_chair_multiview_p2_quad_10000.fbx':
            '02_assets/authoring/school_chair/tripo_quad_source.fbx',
        '07_pipeline/cache/tripo_chair_pilot_20260929/tripo_school_chair_hp_20260929.fbx':
            '02_assets/authoring/school_chair/highpoly_source.fbx',
        '07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_low.fbx':
            '02_assets/authoring/school_chair/baked_low.fbx',
    }
    # 保存可复现的脚本和关键验收；生成日志、测试图和被替代的工程仍属于缓存。
    for row in inventory:
        name = row['path']
        if name.startswith('07_pipeline/cache/') and name.endswith('.py'):
            moves[name] = name.replace('07_pipeline/cache/', '07_pipeline/workflows/', 1)
        elif name.startswith('07_pipeline/cache/') and Path(name).name in {
            'uv_validation.json', 'delivery_validation.json', 'bake_audit.json',
            'school_desk_v4_raw_audit.json', 'approved_shader_interfaces.json'}:
            moves[name] = name.replace('07_pipeline/cache/', '06_review/cloud_assets_20261003/retained_workflow_checks/', 1)
    # SP/烘焙原料随源工程保存，既不是运行时缓存，也不按旧模型的创建日期删除。
    for row in inventory:
        name = row['path']
        for prefix, destination in {
            '07_pipeline/cache/tripo_chair_multiview_20260929/textures/': '02_assets/authoring/school_chair/painter_exports/',
            '07_pipeline/cache/tripo_chair_material_v2_20260930/textures/': '02_assets/authoring/school_chair/baked_exports/',
            '07_pipeline/cache/classroom_props_refresh_20261001/school_desk_v4_structure/': '06_review/cloud_assets_20261003/school_desk_latest/',
        }.items():
            if name.startswith(prefix):
                moves[name] = destination + name[len(prefix):]
    protected = set()
    for row in rows:
        protected.add(row['file'])
        for resource in row['resources']:
            if not resource['packed'] and resource['exists']:
                try:
                    protected.add(Path(resource['absolute']).resolve().relative_to(ROOT).as_posix())
                except ValueError:
                    pass
    deletions = []
    for row in inventory:
        name = row['path']
        if name in moves:
            continue
        reason = None
        if name.startswith('07_pipeline/cache/'):
            reason = '已保留最新源与可复现流程；删除被替代的候选、快照、导出测试和日志'
        elif name.startswith('.local/cloud-smoke/'):
            reason = '独立默认场景烟雾测试生成物'
        elif '__pycache__' in Path(name).parts or Path(name).suffix in {'.pyc', '.pyo', '.blend1', '.blend2'}:
            reason = '字节码或 DCC 自动备份；保留当前工作文件'
        elif name == '06_review/classroom_pipeline_migration_20260929/source_before.blend':
            reason = '本地化迁移前恢复副本，已由当前正式镜头取代'
        if reason:
            assert name not in protected, f'禁止删除仍被保留工程引用的资源: {name}'
            deletions.append(dict(row, reason=reason))
    plan = dict(root=str(ROOT), moves=[dict(source=s, destination=d) for s, d in moves.items()],
                deletions=deletions, protected=sorted(protected),
                delete_files=len(deletions), delete_bytes=sum(r['bytes'] for r in deletions),
                note='未使用资产仅排除上传；不会因镜头未引用而从本机删除。140帧候选在本轮开始前已缺失。')
    (REVIEW / 'cleanup_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: plan[k] for k in ('delete_files', 'delete_bytes')}, ensure_ascii=False))
    print('retained_moves', len(moves))


if __name__ == '__main__':
    main()
