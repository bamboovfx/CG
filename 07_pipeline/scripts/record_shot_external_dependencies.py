"""Record only verified current-shot dependencies for cloud recovery and asset provenance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / '06_review/shot_external_links_20261006'


def read(path):
    """Input JSON path; return UTF-8 data."""
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    """Input JSON path/value; persist readable UTF-8 without changing asset bytes."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    """Consume successful published verification; update manifests and exact dependency whitelist."""
    verification = read(REVIEW / 'published_verification.json')
    dependencies = read(REVIEW / 'dependencies.json')
    assert verification['passed'] and read(REVIEW / 'pixel_comparison.json')['passed']
    files = {row['path']: {k: row[k] for k in ('path', 'bytes', 'sha256')}
             for row in dependencies['textures']}
    for row in verification['other_external_dependencies']:
        files[row['path']] = row
    files[dependencies['geometry']['path']] = {k: dependencies['geometry'][k] for k in ('path', 'bytes', 'sha256')}
    shot = '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
    files[shot] = {'path': shot, 'bytes': verification['bytes'], 'sha256': verification['sha256']}
    manifest = {'date': '2026-10-06', 'scope': 'Published current shot and its actual external dependencies',
                'license_policy': 'Existing asset source licenses inherited; no new media sources added',
                'files': sorted(files.values(), key=lambda row: row['path']),
                'known_missing': verification['existing_unresolved_image_dependencies'],
                'validation': '06_review/shot_external_links_20261006/published_verification.json'}
    write(REVIEW / 'upload_manifest.json', manifest)
    registry = read(ROOT / '00_admin/asset_manifest.json')
    registry['shot_external_links_20261006'] = {
        'source_sha256': dependencies['source_sha256'], 'shot': files[shot],
        'geometry': dependencies['geometry'],
        'textures': [{**row, 'source': 'Exact current-shot payload; inherited prior generated asset provenance',
                      'license': 'Inherited original asset licenses; no new external material acquired'}
                     for row in sorted(files.values(), key=lambda row: row['path']) if row['path'] not in
                     {shot, dependencies['geometry']['path']}],
        'edit_policy': 'External mesh library; local OBJECT material slots and local shader node groups',
        'validation': manifest['validation']}
    write(ROOT / '00_admin/asset_manifest.json', registry)
    ignore = ROOT / '.gitignore'
    current = ignore.read_text(encoding='utf-8')
    lines = ['\n# 2026-10-06：仅放开已验证的镜头外部依赖和验收清单。']
    for path in sorted(files):
        rule = '!/' + path
        if rule not in current.splitlines():
            lines.append(rule)
    for name in ('dependencies.json', 'upload_manifest.json', 'candidate_verification.json',
                 'published_verification.json', 'pixel_comparison.json', 'push_receipt.json'):
        lines.append('!/06_review/shot_external_links_20261006/' + name)
    lines.extend(['\n# 用户指定独立Designer测试仅本机；保留原文件，排除公共同步。',
                  '/.scratch/sd-artstation-test/', '/02_assets/materials/tlou_brick_type_a/',
                  '/06_review/sd_artstation_test_20261006/',
                  '/07_pipeline/scripts/render_sd_brick_test.py',
                  '/07_pipeline/scripts/sd_artstation_brick_test.py',
                  '/07_pipeline/scripts/verify_sd_brick_test.py'])
    ignore.write_text(current.rstrip() + '\n' + '\n'.join(lines) + '\n', encoding='utf-8')
    print('Recorded', len(files), 'unique current-shot dependencies; packed texture images', len(dependencies['textures']))


if __name__ == '__main__':
    main()
