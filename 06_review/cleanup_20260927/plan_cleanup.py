"""生成一次性清理清单，不执行删除；保护当前工程、资源和仍可用的评审入口。"""
import ast
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

ROOT = Path('D:/00_projects/10_CG/Shot_Test').resolve()
OUT = ROOT / '06_review/cleanup_20260927'


def local_links(path):
    """输入 Markdown/HTML 路径，返回存在的项目内链接；网页链接跳过。"""
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    if '04_renders' not in text:
        return
    targets = re.findall(r'\[[^\]]*\]\(([^)]+)\)', text)
    targets += re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)', text)
    for target in targets:
        if '://' in target or target.startswith(('#', '//', '\\\\', 'data:', 'mailto:')):
            continue
        candidate = Path(unquote(target.split('#', 1)[0].strip('<>')))
        resolved = (path.parent / candidate).resolve()
        if resolved.is_relative_to(ROOT) and resolved.is_file():
            yield resolved


def retained_scripts():
    """计算维护、材质生成及当前动画工具的脚本依赖闭包，避免删除仍被导入的模块。"""
    scripts = {p.stem: p for p in (ROOT / '07_pipeline/scripts').glob('*.py')}
    keep = {'build_production_pm', 'production_audit', 'audit_cleanup_dependencies',
            'collect_references', 'collect_artstation_material_references',
            'extract_film_reference_frames', 'render_sh010', 'blackboard_age_masks',
            'blackboard_age_substance', 'blackboard_age_references', 'cloth_tone_simulate',
            'reference_upgrade_research', 'build_sh010', 'render_desk_sd_lookdev'}
    keep |= {s for s in scripts if s.endswith(('_sd', '_textures', '_substance')) or s.startswith('author_')}
    while True:
        previous = set(keep)
        for name in list(keep):
            if name not in scripts:
                continue
            text = scripts[name].read_text(encoding='utf-8-sig')
            for node in ast.walk(ast.parse(text)):
                modules = ([node.module] if isinstance(node, ast.ImportFrom)
                           else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                keep |= {m.split('.')[0] for m in modules if m and m.split('.')[0] in scripts}
            keep |= {s for s in re.findall(r'([A-Za-z_][A-Za-z_0-9]*)\.py', text) if s in scripts}
        if previous == keep:
            return {scripts[s] for s in keep if s in scripts}


def main():
    """读取已完成的依赖审计，逐文件分类并记录删除原因、尺寸和最后修改时间。"""
    audit = json.loads((OUT / 'dependencies_before.json').read_text(encoding='utf-8'))
    assert all(not row['missing_resources'] for row in audit)
    protected = {Path(row['file']).resolve() for row in audit}
    protected |= {Path(p).resolve() for row in audit for p in row['resource_dependencies']}
    scripts = retained_scripts()
    protected |= scripts
    # 当前源文件和上周交付后的新图片一律保留；年代较旧本身不构成资产删除理由。
    retained_cache = {'pose_fit_candidate.blend', 'rest_pose.json', 'reveal_parameters.json'}
    old_blocking = {'blocking.mp4', 'blocking_start_1001.png', 'blocking_middle_1071.png',
                    'blocking_end_1140.png', 'comparison_blocking.jpg', 'probe_1071.png'}
    linked_renders = set()
    for path in (ROOT / '06_review').rglob('*'):
        if path.suffix.lower() in {'.md', '.html'} and '99_archive' not in path.parts and 'candidate' not in path.parts:
            linked_renders |= {p for p in local_links(path) if '04_renders' in p.parts}
    protected |= linked_renders
    published = ROOT / '03_shots/sq010/sh010/publish/drop_sq010_sh010_lighting_v005.blend'
    layout = ROOT / '03_shots/sq010/sh010/work/drop_sq010_sh010_layout.blend'
    identical_publish = published.exists() and hashlib.sha256(published.read_bytes()).digest() == hashlib.sha256(layout.read_bytes()).digest()
    items = []
    total_files = total_bytes = 0
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        assert not path.is_symlink()
        st = path.stat()
        total_files += 1
        total_bytes += st.st_size
        rel = path.relative_to(ROOT).as_posix()
        reason = None
        if path in protected:
            continue
        if rel.startswith('07_pipeline/cache/'):
            if rel.startswith('07_pipeline/cache/tools/imageio_ffmpeg'):
                continue  # 当前动画编码脚本仍使用该运行时。
            if rel.startswith('07_pipeline/cache/sh010_blocking_20260920/') and path.name in retained_cache:
                continue
            reason = '过时缓存、候选工程、旧阶段快照或下载工具缓存'
        elif re.search(r'\.blend\d+$', path.name) or '.autosave' in path.parts or '__pycache__' in path.parts:
            reason = '自动备份或可重新生成的解释器缓存'
        elif rel.startswith('99_archive/'):
            reason = '已被当前工程和规范替代的历史版本副本'
        elif rel.startswith('03_shots/sq010/sh010/cache/'):
            reason = '早期v001至v005构建与渲染日志'
        elif path == published and identical_publish:
            reason = '旧v005发布文件与保留的Layout字节完全相同'
        elif rel.startswith('06_review/production_plan_20260920/candidate/'):
            reason = '已启用规范的旧候选副本'
        elif rel.startswith(('06_review/sh010_blocking_20260920/frames/', '06_review/sh010_blocking_20260920/pose_fit_frames/')):
            reason = '已编码并验证的视频中间PNG序列，保留视频与首中末帧'
        elif rel.startswith('06_review/sh010_blocking_20260920/') and path.name in old_blocking:
            reason = '被坐姿修正版替代的旧灰模预览；综合对照图保留'
        elif rel.startswith('04_renders/') and datetime.fromtimestamp(st.st_mtime) < datetime(2026, 9, 21):
            reason = '未被保留文档链接使用的旧测试渲染'
        elif path.parent == ROOT / '07_pipeline/scripts' and path.suffix == '.py' and path not in scripts:
            reason = '已完成阶段的一次性修改、探测、提交或评审脚本'
        if reason:
            items.append({'path': rel, 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
                          'mtime_ticks': st.st_mtime_ns // 100 + 621355968000000000, 'reason': reason})
    data = {'root': str(ROOT), 'created_at': datetime.now().astimezone().isoformat(),
            'before_file_count': total_files, 'before_bytes': total_bytes,
            'protected_sources': [{'path': row['file'], 'sha256': row['sha256']} for row in audit],
            'protected_resources': sorted(str(p) for p in protected if p.exists()),
            'kept_scripts': sorted(p.relative_to(ROOT).as_posix() for p in scripts),
            'items': items, 'planned_bytes': sum(i['bytes'] for i in items),
            'policy': '保留全部正式贴图和材质源；打开中的Blender未保存依赖未完整读取，资源池不按未引用推断删除。'}
    (OUT / 'manifest.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(items), 'GiB': round(data['planned_bytes'] / 2**30, 3),
                      'kept_scripts': len(scripts), 'reasons': dict(Counter(i['reason'] for i in items))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
