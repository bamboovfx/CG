"""记录正式课椅替换的来源、哈希和依赖；只更新资产清单中的本轮条目。"""
from pathlib import Path
import hashlib
import json


def sha256_file(path):
    """输入本地文件路径，分块读取并返回SHA256，避免大打包资产一次占用内存。"""
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    """输入实际发布和重开证据，输出项目资产清单中的来源记录；保留已有清单字段。"""
    project = Path(__file__).resolve().parents[2]
    review = project / '06_review/chair_scene_replace_20261001'
    published = json.loads((review / 'published.json').read_text(encoding='utf-8'))
    checked = json.loads((review / 'published_validation.json').read_text(encoding='utf-8'))
    assert checked['passed']
    source = project / '07_pipeline/cache/chair_scene_replace_20261001/approved_chair_live.blend'
    path = project / '00_admin/asset_manifest.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['scene_chair_replace_20261001'] = {
        'date': '2026-10-01',
        'source': source.relative_to(project).as_posix(),
        'source_sha256': sha256_file(source),
        'target': '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend',
        'target_sha256': published['after_sha256'],
        'chairs': checked['chairs'], 'parts': checked['parts'],
        'materials': checked['materials'], 'valid_seed_drivers': checked['valid_drivers'],
        'source_policy': 'Reuses user-approved Tripo model and existing authored SD/imagegen material content; no new external media or texture downloads.',
        'license_policy': 'Inherited source asset provenance and licenses; reference photographs remain reference material and are not declared redistributable.',
        'review': '06_review/chair_scene_replace_20261001/report.md',
        'validation': '06_review/chair_scene_replace_20261001/published_validation.json',
        'status': 'published_technical_verified_scene_visual_review_pending'
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Recorded scene chair publication provenance.')


if __name__ == '__main__':
    main()
