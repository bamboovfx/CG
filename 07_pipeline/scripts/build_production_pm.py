"""从 Markdown 任务卡生成只读 PM 看板；校验依赖和完成证据，不修改任务状态。"""
import argparse
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('State', 'Status', 'Owner', 'Type', 'Blocked by', 'Updated')
STATES = {'backlog', 'ready', 'in-progress', 'review', 'blocked', 'done', 'cancelled'}


def links(value):
    """输入 Markdown 字符串，返回具名链接列表；仅供项目内文档关系解析。"""
    return re.findall(r'\[([^\]]+)\]\(([^)]+)\)', value)


def read_card(path):
    """输入任务路径，返回标题、状态字段、验收项和证据链接。"""
    text = path.read_text(encoding='utf-8-sig')
    card = {'path': path, 'title': text.splitlines()[0].lstrip('# '), 'text': text}
    for field in FIELDS:
        match = re.search(rf'^{re.escape(field)}: (.*)$', text, re.M)
        if not match:
            raise ValueError(f'{path}: 缺少 {field}')
        card[field] = match.group(1).strip()
    card['dependencies'] = [(path.parent / target).resolve() for _, target in links(card['Blocked by'])]
    section = text.split('## Evidence', 1)[-1].split('\n## ', 1)[0]
    card['evidence'] = links(section) if '## Evidence' in text else []
    card['checks'] = re.findall(r'^- \[([ x])\] (.+)$', text, re.M)
    return card


def resolve_evidence(card, target, source):
    """输入证据链接和候选根目录；候选未含资源时解析到真实项目同相对路径。"""
    path = (card['path'].parent / target).resolve()
    if not path.is_file() and path.is_relative_to(source):
        path = ROOT / path.relative_to(source)
    return path


def validate(cards, source):
    """输入卡片与源目录，返回依赖/证据检查结果；失败阻止生成看板。"""
    by_path = {card['path']: card for card in cards}
    errors = []
    for card in cards:
        if card['State'] not in STATES:
            errors.append(f"非法 State: {card['path']}")
        for dep in card['dependencies']:
            if dep not in by_path:
                errors.append(f"不存在的前置: {card['title']} -> {dep}")
            elif card['State'] in {'ready', 'in-progress', 'review', 'done'} and by_path[dep]['State'] != 'done':
                errors.append(f"越过前置: {card['title']} -> {by_path[dep]['title']}")
        if card['State'] == 'done':
            if not card['checks'] or any(check != 'x' for check, _ in card['checks']):
                errors.append(f"完成卡仍有未通过验收: {card['title']}")
            if not card['evidence']:
                errors.append(f"完成卡没有证据: {card['title']}")
        for _, target in card['evidence']:
            if not resolve_evidence(card, target, source).is_file():
                errors.append(f"证据不存在: {card['title']} -> {target}")
    visiting, visited = set(), set()

    def visit(path):
        """深度遍历一个任务路径，记录依赖循环；不重复访问已完成节点。"""
        if path in visiting:
            errors.append(f'依赖循环: {path}')
            return
        if path in visited or path not in by_path:
            return
        visiting.add(path)
        for dep in by_path[path]['dependencies']:
            visit(dep)
        visiting.remove(path)
        visited.add(path)

    for path in by_path:
        visit(path)
    return {'checked_at': datetime.now().astimezone().isoformat(), 'card_count': len(cards),
            'errors': errors, 'passed': not errors}


def main():
    """按 --source 读取真实或候选任务，输出 HTML 与校验 JSON；--draft 显示待确认标记。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--draft', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    cards = [read_card(path.resolve()) for path in sorted(source.glob('.scratch/*/issues/*.md'))]
    assert cards, '没有任务卡，不能生成空看板。'
    result = validate(cards, source)
    out = source / '00_admin/pm'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    assert result['passed'], result['errors']

    # 下一步随任务状态变化；不能把某次会话的 Blocking 阶段写死在生成器。
    priority = {'review': 0, 'in-progress': 1, 'ready': 2, 'blocked': 3, 'backlog': 4}
    open_cards = [card for card in cards if card['State'] not in {'done', 'cancelled'}]
    open_cards.sort(key=lambda card: priority[card['State']])
    current = open_cards[0] if open_cards else None
    next_title = current['title'] if current else '当前任务组已完成验收'
    next_text = (current['text'].split('## Next', 1)[-1].split('\n## ', 1)[0].strip()
                 if current and '## Next' in current['text'] else '读取制作路线图，选择下一个已解锁任务。')

    def anchor(label, path):
        """输入标签和本地文件路径，返回以看板目录为基准的安全HTML链接。"""
        href = os.path.relpath(path, out).replace('\\', '/')
        return f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'

    # 优先展示当前任务证据中列出的第一条视频，版本归属由任务卡控制。
    video_preview = ''
    if current:
        videos = [(label, resolve_evidence(current, target, source))
                  for label, target in current['evidence'] if Path(target).suffix.lower() == '.mp4']
        if videos:
            label, path = videos[0]
            video_href = os.path.relpath(path, out).replace('\\', '/')
            video_preview = (f'<h2>{html.escape(label)}</h2><video controls muted loop preload="metadata" '
                             f'style="width:100%;max-height:560px;background:#000" '
                             f'src="{html.escape(video_href, quote=True)}"></video>')

    names = {'backlog': '待前置', 'ready': '可开始', 'in-progress': '制作中', 'review': '待审阅',
             'blocked': '有阻塞', 'done': '已通过', 'cancelled': '已取消'}
    rows = []
    for card in cards:
        deps = ', '.join(label for label, _ in links(card['Blocked by'])) or '无'
        evidence = ' · '.join(anchor(label, resolve_evidence(card, target, source)) for label, target in card['evidence']) or '尚未交付'
        done = sum(check == 'x' for check, _ in card['checks'])
        rows.append(f'<tr><td>{anchor(card["title"], card["path"])}<small>{html.escape(card["path"].parts[-3])}</small></td>'
                    f'<td><span class="state {card["State"]}">{names[card["State"]]}</span></td>'
                    f'<td>{html.escape(card["Owner"])}</td><td>{html.escape(deps)}</td>'
                    f'<td>{done}/{len(card["checks"])} 项</td><td>{evidence}</td></tr>')
    reference = ROOT / '06_review/production_audit_20260920'
    hero_image = os.path.relpath(reference / 'current_main.png', out).replace('\\', '/')
    warning = '<div class="notice">草案 · 跟踪方式、默认标签和任务拆分待用户确认；当前正式规范尚未替换。</div>' if args.draft else ''
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>dro:p 制作看板</title><style>
body{{margin:0;background:#111a1c;color:#e2e8e7;font:15px/1.65 "Microsoft YaHei",sans-serif}}main{{max-width:1360px;margin:auto;padding:38px}}h1{{font-size:32px;margin:4px 0}}h2{{font-size:19px;margin-top:30px}}a{{color:#a8d8c6;text-decoration:none}}a:hover{{text-decoration:underline}}p{{max-width:980px}}.muted,small{{color:#9eb3b3}}small{{display:block;font-size:11px}}.notice{{padding:12px 18px;background:#473d26;color:#f5d792;border-radius:8px;margin:20px 0}}.stats{{display:flex;gap:18px;flex-wrap:wrap;margin:24px 0}}.stat{{border:1px solid #344747;border-radius:9px;padding:16px 24px;min-width:155px}}.stat strong{{display:block;font-size:25px}}.hero{{width:100%;border-radius:8px;display:block}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{text-align:left;padding:13px;border-bottom:1px solid #344747;vertical-align:top}}th{{color:#9eb3b3;font-weight:400}}.state{{white-space:nowrap;padding:3px 8px;border-radius:5px;background:#2a3637}}.in-progress{{background:#26544c}}.review{{background:#695127}}.done{{background:#30473a}}.scroll{{overflow-x:auto}}footer{{margin-top:35px;padding-top:20px;border-top:1px solid #344747;color:#9eb3b3;font-size:12px}}
</style><main><div class="muted">初版CG镜头测试 / 证据优先</div><h1>Drop关键镜头 → 个人短片</h1>
<p>先复刻关键镜头验证制作能力，再完成自己的短片镜头。当前推进主教室140帧测试；全片参考用于选题，已选制作范围与阶段目标见项目说明。</p>{warning}
<div class="stats"><div class="stat"><strong>140 帧</strong>当前镜头 · 24 fps · 5.83秒</div><div class="stat"><strong>1 条</strong>主要制作 WIP 上限</div><div class="stat"><strong>6027 帧</strong>原片研究范围 · 不计制作完成率</div><div class="stat"><strong>待选择</strong>后续关键镜头与原创分镜</div></div>
<p>{anchor('当前镜头规格', source/'.scratch/sh010-test/spec.md')} · {anchor('制作规范', source/'00_admin/production_standard.md')} · {anchor('项目范围与能力证据', source/'00_admin/project_brief.md')} · {anchor('制作路线图', source/'.scratch/drop-film/map.md')}</p>
<h2>当前下一步 · {html.escape(next_title)}</h2><p>{html.escape(next_text)}</p>
<div class="scroll"><table><thead><tr><th>任务</th><th>状态</th><th>负责人</th><th>前置</th><th>验收</th><th>证据</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
{video_preview}
<h2>2026-09-20 审计时的静帧基线</h2><img class="hero" src="{html.escape(hero_image, quote=True)}" alt="2026年9月20日正式镜头的主机位基线"><p class="muted">1920×810 / Cycles 32 spp评审。图像说明当时的制作起点，后续进度与交付看上方任务卡。</p>
<p>{anchor('场景读回检查', reference/'scene_audit.json')} · {anchor('全片参考清单', reference/'full_film_shot_inventory.md')} · {anchor('相机与人物相对运动证据', reference/'hero_motion_guide.md')}</p>
<h2>能力结论怎么记</h2><p>每项任务记录问题、工具与人工介入、结果证据、失败纠正和可迁移做法。第一次拉片把相机揭示误判为角色走入，已由人物和椅子的相对位置核对纠正；这项限制保留在记录中。</p>
<footer>任务卡是状态权威；本页由 build_production_pm.py 生成，不直接修改状态。已验证 {len(cards)} 张卡的依赖、循环、完成验收与现有证据。生成时间 {result['checked_at']}。</footer></main></html>'''
    (out / 'index.html').write_text(page, encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
