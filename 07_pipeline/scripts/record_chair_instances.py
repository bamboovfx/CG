"""登记共享实例课椅的实际发布来源、数据量与哈希；保留清单历史条目。"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_scene_chair_publication import sha256_file


def main():
    """输入本轮实际发布及正式重开证据，输出资产清单新条目；不修改任何Blender文件。"""
    project = Path(__file__).resolve().parents[2]
    review = project / '06_review/chair_instances_20261001'
    published = json.loads((review / 'published.json').read_text(encoding='utf-8'))
    verified = json.loads((review / 'published_validation.json').read_text(encoding='utf-8'))
    assert verified['passed']
    backup = project / '07_pipeline/cache/chair_instances_20261001/before_instances.blend'
    path = project / '00_admin/asset_manifest.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['scene_chair_instances_20261001'] = {
        'date': '2026-10-01',
        'source': '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend',
        'source_before_sha256': published['before_sha256'],
        'before_backup': backup.relative_to(project).as_posix(),
        'before_backup_sha256': sha256_file(backup),
        'published_sha256': published['after_sha256'],
        'instances': 25, 'counts_before': verified['before'], 'counts_after': verified['after'],
        'source_policy': 'Reuses existing approved Tripo geometry and authored SD/imagegen maps. Shared mother collection; instancer attributes drive procedural wear and grain sampling. No new external media.',
        'license_policy': 'Existing source licenses and provenance inherited; reference photographs remain reference-only.',
        'edit_scene': 'Chair_Asset_Edit',
        'validation': '06_review/chair_instances_20261001/published_validation.json',
        'review': '06_review/chair_instances_20261001/report.md',
        'status': 'published_technical_verified_scene_visual_review_pending'
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Recorded shared chair instance publication.')


if __name__ == '__main__': main()
