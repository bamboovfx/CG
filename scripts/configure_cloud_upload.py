"""从镜头依赖生成 uGit 可见的上传白名单、LFS 属性及可审计清单。"""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / '06_review/cloud_assets_20261003'


def digest(path):
    """输入文件路径；流式返回 SHA256，供 LFS 去重与传输后核对。"""
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    """输入依赖审计；输出精确白名单，默认不上传未使用资产、缓存、原片和参考。"""
    rows = json.loads((REVIEW / 'dependencies_before.json').read_text(encoding='utf-8'))
    selected = {'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend': '当前权威镜头',
                '02_assets/work/school_chair.blend': '镜头已采用的最新独立课椅编辑源'}
    referenced = set()
    for row in (rows[0], rows[2]):
        for resource in row['resources']:
            if resource['exists']:
                try:
                    name = Path(resource['absolute']).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    continue
                referenced.add(name)
                if not resource['packed']:
                    selected[name] = '正式镜头外部依赖'
    # 原生材质图是已验证流程的可编辑配方；仅收录当前资产族及其显式图片输入。
    family_map = {'architecture_rebuild': 'architecture_sd', 'architecture_corridor': 'architecture_corridor_sd',
                  'equipment_rebuild': 'equipment_sd', 'hero_tin': 'hero_tin_sd',
                  'shell_tin_rebuild': 'shell_tin_sd', 'teaching_rebuild': 'teaching_sd',
                  'school_desk': 'school_desk_sd'}
    inputs = set()
    for path in sorted((ROOT / '02_assets/materials').rglob('*.sbs')):
        family = path.relative_to(ROOT / '02_assets/materials').parts[0]
        generated = family_map.get(family, family)
        if not any(f'/generated/{generated}/' in name for name in referenced):
            continue
        selected[path.relative_to(ROOT).as_posix()] = '当前资产使用的原生 Substance 材质流程'
        for element in ET.parse(path).iter():
            if element.tag != 'filepath':
                continue
            value = element.get('v', '')
            absolute = Path(value) if Path(value).is_absolute() else path.parent / value
            if absolute.is_file():
                try:
                    name = absolute.resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    continue
                selected[name] = '已保留原生 SBS 图的图片输入'
                inputs.add(name)
            elif value:
                raise FileNotFoundError(f'SBS 外部输入缺失: {path.name}: {value}')
    # 随资产收录来源清单，保留许可、来源与哈希；不上传参考网站照片或系统字体。
    for name in list(selected):
        parent = (ROOT / name).parent
        while parent != ROOT and parent.is_relative_to(ROOT / '02_assets'):
            for metadata in parent.glob('*manifest.json'):
                selected[metadata.relative_to(ROOT).as_posix()] = '入选资产来源与许可记录'
            parent = parent.parent
    selected['00_admin/asset_manifest.json'] = '项目素材来源与许可总清单'
    selected['07_pipeline/config/project.json'] = '项目本机配置及根目录语义'
    for path in (ROOT / 'docs/cloud').glob('*.json'):
        selected[path.relative_to(ROOT).as_posix()] = '云端配置'
    for path in REVIEW.rglob('*.json'):
        if path.name != 'upload_manifest.json':
            selected[path.relative_to(ROOT).as_posix()] = '本轮清理、迁移和验证证据'
    files = []
    duplicates = defaultdict(list)
    for name, reason in sorted(selected.items()):
        path = ROOT / name
        assert path.is_file(), name
        sha = digest(path)
        files.append(dict(path=name, bytes=path.stat().st_size, sha256=sha, reason=reason))
        duplicates[sha].append(name)
    excluded = [p.relative_to(ROOT).as_posix() for p in (ROOT / '02_assets').rglob('*')
                if p.is_file() and p.relative_to(ROOT).as_posix() not in selected
                and p.suffix not in {'.md', '.py', '.html'}]
    result = dict(repository='bamboovfx/CG', policy='shot_dependencies_and_current_editable_workflows',
                  files=files, bytes=sum(f['bytes'] for f in files),
                  identical_content_groups=[dict(sha256=k, paths=v) for k, v in duplicates.items() if len(v) > 1],
                  excluded_local_assets=sorted(excluded),
                  known_missing=[r for r in rows[0]['resources'] if not r['packed'] and not r['exists']],
                  external_system_resources=[r for r in rows[0]['resources']
                                             if r['exists'] and not r['packed'] and r['kind'] == 'fonts'])
    (REVIEW / 'upload_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    selected['06_review/cloud_assets_20261003/upload_manifest.json'] = '上传范围与哈希清单'
    rules = ['# 默认只同步文档、工具及下方已审计的镜头资产；uGit 与 CLI 共用此白名单。',
             '*', '!*/', '!*.md', '!*.py', '!*.sh', '!*.ps1', '!*.html', '!*.css', '!*.js',
             '!.gitignore', '!.gitattributes', '# 当前镜头、外部依赖及可编辑材质配方。']
    rules.extend('!/' + name.replace('[', '\\[').replace(']', '\\]') for name in sorted(selected))
    rules.extend(['# 永久本地范围；新资产需先核查依赖再加入白名单。',
                  '/.local/', '/04_renders/', '/05_comp/', '/07_pipeline/cache/', '/99_archive/',
                  '**/__pycache__/', '**/node_modules/', '**/.git/', '**/.env*', '**/.sandbox-secrets/',
                  '*.py[cod]', '*.blend[0-9]*', '*_autosave_*', '*.tmp', '*.log', '**/api_inspection*'])
    (ROOT / '.gitignore').write_text('\n'.join(rules) + '\n', encoding='utf-8')
    attributes = ['# 脚本统一换行；工程、贴图与其他二进制交由 LFS 管理。',
                  '*.sh text eol=lf', '*.py text eol=lf', '*.ps1 text eol=lf', '*.sbs text eol=lf']
    attributes.extend(f'*.{extension} filter=lfs diff=lfs merge=lfs -text'
                      for extension in ('blend', 'fbx', 'glb', 'gltf', 'spp', 'sbsar', 'png', 'jpg', 'jpeg',
                                        'webp', 'exr', 'hdr', 'tif', 'tiff', 'mp4', 'mov', 'usd', 'usdc'))
    (ROOT / '.gitattributes').write_text('\n'.join(attributes) + '\n', encoding='utf-8')
    # LFS 相同内容共享一个对象；资源路径可能有不同语义，不能删除仍被节点引用的同内容图片。
    print(json.dumps(dict(files=len(files), GiB=round(result['bytes'] / 1024**3, 3),
                          identical_groups=len(result['identical_content_groups']),
                          excluded_local_assets=len(excluded), sbs_inputs=len(inputs)), ensure_ascii=False))


if __name__ == '__main__':
    main()
