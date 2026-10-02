"""汇总已有参考，用 PureRef 官方 CLI 生成内嵌、独立图片的原生画板。

输入：项目现有参考与来源清单。输出：.pur、位置/来源清单、总览。
原图不改写；SHA256 或完全相同的解码像素合并，别名保留在清单中。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
from collections import defaultdict

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / '01_preproduction/references'
AUDIT = ROOT / '06_review/production_audit_20260920'
OUT = ROOT / '01_preproduction/reference_board'
CACHE = ROOT / '07_pipeline/cache/pureref_board'
EXE = Path('D:/Program Files/PureRef/PureRef.exe')
BOARD = OUT / 'drop_all_references.pur'
EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}
WIDTH, GAP, COLS = 9000, 420, 6


def rel(path):
    """输入项目路径，返回可移植的相对路径字符串。"""
    return path.relative_to(ROOT).as_posix()


def read_json(path):
    """读本地 JSON（兼容 BOM），返回文档；非 JSON 则返回空字典。"""
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        return {}


def candidate_paths():
    """返回明确属于参考的图片；评审渲染、贴图和 Blender UI 截图不收录。"""
    paths = set(p for p in REFS.rglob('*') if p.suffix.lower() in EXTS)
    paths.update(p for p in AUDIT.glob('*') if p.suffix.lower() in EXTS and p.name != 'current_main.png')
    for folder in [AUDIT/'frames', AUDIT/'hero_motion_frames']:
        paths.update(p for p in folder.iterdir() if p.suffix.lower() in EXTS)
    paths.update((ROOT/'06_review/architecture_rebuild').glob('reference_*'))
    paths.add(ROOT/'06_review/cloth_tone/reference.png')
    for folder in ['equipment_rebuild/references', 'equipment_rebuild/hero_tin/references',
                   'teaching_rebuild/references', 'teaching_rebuild/material_references']:
        paths.update(p for p in (ROOT/'06_review'/folder).rglob('*') if p.suffix.lower() in EXTS)
    return sorted(p for p in paths if p.is_file() and p.suffix.lower() in EXTS)


def provenance(paths):
    """匹配已有来源 JSON；继承作者/页面信息，仅在路径明确或局部文件名唯一时关联。"""
    found = defaultdict(list)
    jsons = list(REFS.rglob('*.json'))
    for folder in ['equipment_rebuild', 'teaching_rebuild', 'architecture_rebuild']:
        jsons += list((ROOT/'06_review'/folder).rglob('*sources*.json'))

    def walk(value, source, inherited=None):
        """递归来源记录，将父级页面、作者和许可传给图片条目。"""
        if isinstance(value, list):
            for child in value:
                walk(child, source, inherited)
        elif isinstance(value, dict):
            context = dict(inherited or {})
            for key in ['title', 'owner', 'license', 'rights', 'note', 'use', 'page', 'page_url', 'source_page', 'url']:
                if isinstance(value.get(key), str):
                    if key == 'url' and value[key].split('?')[0].lower().endswith(tuple(EXTS)):
                        context['image_url'] = value[key]
                    else:
                        context[key] = value[key]
            for key in ['path', 'file', 'filename', 'image']:
                name = value.get(key)
                if not isinstance(name, str) or name.startswith('http') or Path(name).suffix.lower() not in EXTS:
                    continue
                possibles = [(ROOT/name).resolve(), (source.parent/name).resolve()]
                matches = [p for p in paths if p.resolve() in possibles]
                if not matches:
                    matches = [p for p in paths if p.name == Path(name).name and p.is_relative_to(source.parent)]
                if len(matches) == 1:
                    record = {'source_manifest': rel(source), **context}
                    if record not in found[rel(matches[0])]:
                        found[rel(matches[0])].append(record)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child, source, context)
    for source in jsons:
        walk(read_json(source), source)
    return found


def classification(path):
    """按图片来源与用途返回大区、分组、中文标题。"""
    name = rel(path)
    if path.parent == AUDIT/'frames':
        frame = int(re.search(r'\d+', path.stem).group())
        for item in read_json(AUDIT/'full_film_shot_inventory.json')['entries']:
            if item['source_start_frame'] <= frame < item['source_end_frame_exclusive']:
                return 5, item['reference_id'], item['reference_id']+' · '+item['visual_description']
        raise ValueError(f'源帧不在审计范围: {name}')
    if path.parent == AUDIT/'hero_motion_frames':
        return 3, 'hero_frames', '主教室全景 · 动作逐帧 / REF027'
    if path.parent == AUDIT:
        if path.name.startswith(('hero_', 'classroom_', 'rear_', 'female_')):
            return 3, 'hero_analysis', '主教室 · 动作与遮挡分析图'
        family = path.stem.split('_')[0]
        titles = {'additional':'补充切点','cut':'切点对照','dark':'暗部连续性','dense':'密集转场',
                  'ending':'结尾连续性','overview':'全片概览','shop':'商店连续性','existing':'早期接触表'}
        return 4, 'analysis_'+family, '全片 · '+titles.get(family,family)
    if '/artstation/' in name:
        artist = path.parent.name
        return 1, artist, 'ArtStation · '+artist.replace('_', ' ').title()
    if '/classroom_research_' in name:
        if path.name.startswith('ykk_'):
            return 2, 'hardware', '窗户五金 · 尺寸 / 安装 / 剖面'
        if path.stem in ['user_reference_1', 'user_reference_2', 'user_reference_3']:
            return 0, 'corridor', '原片 · 走廊与 Breakdown'
        if path.stem == 'user_reference_4':
            return 0, 'golden', '原片 · 教室光色 / 用户提供'
        return 0, 'film_frames', '原片 · 教室与关键场景截图'
    if '/golden_light_' in name:
        return 0, 'golden', '原片 · 教室光色 / 用户提供'
    if '/corridor_' in name:
        return 0, 'corridor', '原片 · 走廊与 Breakdown'
    if '/film/' in name:
        return 0, 'film_stills', '原片 · 官方剧照与教室机位'
    if '/video/' in name:
        return 4, 'video_contacts', '原片 · 早期拉片与补充帧'
    if '/window_hardware_' in name:
        return 2, 'hardware', '窗户五金 · 尺寸 / 安装 / 剖面'
    if '/blackboard_age_' in name or path.name == 'erased_chalk_surface.jpg':
        return 2, 'blackboard', '黑板 · 涂层工艺 / 褪色 / 擦拭残留'
    if '/wood_groups/' in name or '/material_studies/shell/' in name or 'cabinet_' in path.name or 'wood_edge' in path.name or 'beech' in path.name:
        return 2, 'wood', '木材 · 分组 / 涂装 / 边缘磨损'
    if '/metal_response/' in name:
        return 2, 'metal', '金属 · 喷漆钢管 / 拉丝五金'
    if '/architecture_rebuild/' in name and path.name not in ['reference_window.png', 'reference_concrete_school_corridor.png']:
        return 2, 'curtains', '窗帘 · 布料 / 吊轨 / 风动'
    if '/architecture/' in name or '/architecture_rebuild/' in name:
        return 2, 'architecture', '实景建筑 · 窗户与走廊'
    if '/hero_tin/' in name:
        return 2, 'tin', '铁盒角色 · 实物包装与形体'
    if '/black_clock/' in name or '/tv_screen/' in name or 'Clock_' in path.name or path.name in ['clock.jpg', 'fluorescent.jpg']:
        return 2, 'equipment', '室内设备 · 时钟 / 电视 / 灯具'
    if '/props/' in name or '/teaching_rebuild/references/' in name:
        return 2, 'furniture', '课桌椅与讲台 · 结构 / 木作'
    if '/cloth_tone/' in name:
        return 0, 'golden', '原片 · 教室光色 / 用户提供'
    return 2, 'surfaces', '细节材质 · 纸张 / 书本 / 抹灰 / 粉尘'


def inventory():
    """清点尺寸与哈希，合并严格重复并保存所有原路径和来源。"""
    paths = candidate_paths()
    sources = provenance(paths)
    seen, unique = {}, []
    # 主参考优先：重复图放入主用途分区，低成本拉片里的重复黑帧只保留一次。
    paths.sort(key=lambda p: (classification(p)[0], rel(p)))
    for path in paths:
        with Image.open(path) as raw:
            im = ImageOps.exif_transpose(raw).convert('RGBA')
            key = hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
            size = list(im.size)
        alias = {'path': rel(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'provenance': sources.get(rel(path), [])}
        if not alias['provenance'] and path.is_relative_to(AUDIT):
            alias['provenance']=[{'source_video':'01_preproduction/references/video/drop_official_1080p.mp4',
                'fps':24,'source_inventory':rel(AUDIT/'full_film_shot_inventory.json'),
                'kind':'原片源帧或以原片帧制作的分析图；按目录和文件名区分','rights':'原作者版权；本地研究'}]
        if key in seen:
            seen[key]['originals'].append(alias)
        else:
            section, group, title = classification(path)
            rec = {'id':f'R{len(unique)+1:04d}', 'path':rel(path), 'size':size, 'pixel_sha256':key,
                   'section':section, 'group':group, 'group_title':title, 'originals':[alias]}
            unique.append(rec)
            seen[key] = rec
    return paths, unique


def card(name, width, lines, color='#193b47', font=110, pad=110):
    """创建文字导航 SVG，返回路径与尺寸；参考图本身完全不改动。"""
    height = pad*2 + sum(size*1.5 for _, size in lines)
    xml = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
           f'<rect width="100%" height="100%" rx="32" fill="{color}"/>']
    y = pad
    for text, size in lines:
        y += size*1.2
        xml.append(f'<text x="{pad}" y="{y}" font-family="Microsoft YaHei,Arial" font-size="{size}" fill="#eef3ec">{html.escape(text)}</text>')
        y += size*.3
    xml.append('</svg>')
    path = CACHE/'labels'/f'{name}.svg'
    path.write_text('\n'.join(xml),encoding='utf-8')
    return path, width, height


def arrange(records):
    """分区按行排列原图，标题、图片与图注各占独立矩形，返回所有 CLI 图片位置。"""
    nodes, bounds, groups = [], [], defaultdict(list)
    for rec in records:
        groups[(rec['section'],rec['group'])].append(rec)

    def add(path, x, y, w, h, kind, ident):
        """登记左上坐标与尺寸，CLI 使用中心坐标。"""
        nodes.append({'path':rel(path), 'x':x+w/2, 'y':y+h/2,'width':w,'height':h,'kind':kind,'id':ident})

    sections = [
        ('01 / 原片视觉基准', '暖教室、冷走廊；先对构图、比例、光向，再看细节。', '#34504b'),
        ('02 / ArtStation 案例', '按作者分开；结构与工艺可参考，色调仍以原片为准。', '#333f59'),
        ('03 / 实物与工艺', '窗户五金、布料、黑板、木材、金属、家具与设备。', '#56452d'),
        ('04 / 主教室动态研究', '原片 REF027：3823–3963，Out 不含；140 帧 / 24 fps。', '#493d56'),
        ('05 / 全片分析图', '既有转场、机位与连续性接触表；分析标记不是原片内容。', '#3c4753'),
        ('06 / 全片逐帧资料', '按 REF001–044 排序；参考容器不等于最终制作镜头数。', '#3f4748'),
    ]
    y0 = 0
    total_width = COLS*WIDTH+(COLS-1)*GAP
    for section, (heading, note, color) in enumerate(sections):
        cp,w,h = card(f'section_{section}',WIDTH,[(heading,330),(note,115)],color)
        add(cp,0,y0,w,h,'section',str(section))
        if section == 0:
            cp,ww,hh = card('board_guide',WIDTH,[(f'dro:p / 参考资料总板',310),('2026-09-28 · 现有资料归档',160),
                (f'{len(records)} 张独立参考图 · 原图内嵌 · 严格重复合并',130),('滚轮缩放；中键拖动画布；选中图片后 Space 聚焦',110),
                ('详细来源与重复路径：旁边的 manifest.json / index.html',110)],'#292e33')
            add(cp,WIDTH+GAP,y0,ww,hh,'guide','guide')
            h=max(h,hh)
        y0+=h+350
        keys=sorted(key for key in groups if key[0]==section)
        # 四列逐行排列；读序固定，避免瀑布流打乱原片时间顺序。
        for row in range(0,len(keys),COLS):
            heights=[]
            for col,key in enumerate(keys[row:row+COLS]):
                items=groups[key]; x0=col*(WIDTH+GAP); gy=y0
                title=items[0]['group_title']; details=f'{len(items)} 张 · 图注编号对应来源清单'
                if section==5:
                    entry=next(e for e in read_json(AUDIT/'full_film_shot_inventory.json')['entries'] if e['reference_id']==key[1])
                    details=f"{entry['in_timecode']} → {entry['out_timecode_exclusive']} (Out不含) / {len(items)} 张"
                cp,w,h=card(f'group_{section}_{key[1]}',WIDTH,[(title,155),(details,95)],color,pad=90)
                add(cp,x0,gy,w,h,'group',key[1]); gy+=h+150
                x=x0; row_height=0
                for rec in items:
                    w,h=rec['size']
                    if w>WIDTH:
                        raise ValueError(f'图片比列宽大，需扩大列宽: {rec["path"]}')
                    if x>x0 and x+w>x0+WIDTH:
                        gy+=row_height+145; x=x0; row_height=0
                    rec['rect']=[x,gy,w,h]
                    add(ROOT/rec['path'],x,gy,w,h,'reference',rec['id'])
                    fontsize=min(46,max(12,w/55))
                    caption=f'{rec["id"]} | {Path(rec["path"]).name}'
                    caption=caption[:70]
                    cp,cw,ch=card('caption_'+rec['id'],w,[(caption,fontsize)],'#282b2e',pad=fontsize*.4)
                    add(cp,x,gy+h+12,cw,ch,'caption',rec['id'])
                    row_height=max(row_height,h+12+ch); x+=w+130
                height=gy+row_height-y0
                bounds.append({'section':section,'group':key[1],'title':title,'count':len(items),'rect':[x0,y0,WIDTH,height]})
                heights.append(height)
            y0+=max(heights)+400
        y0+=700
    return nodes,bounds,[total_width,y0]


def run_cli(commands, timeout=180):
    """以隐藏的新进程执行 PureRef 文档化 CLI；错误或超时不继续发布。"""
    args=[str(EXE)]
    for command in commands:
        args+=['-c',command]
    si=subprocess.STARTUPINFO(); si.dwFlags|=subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=0
    result=subprocess.run(args,cwd=ROOT,startupinfo=si,capture_output=True,timeout=timeout)
    log=(result.stdout+result.stderr).decode(errors='replace')
    if '[Warning]' in log:
        with (CACHE/'cli_warnings.txt').open('a',encoding='utf-8') as stream:
            stream.write('\n'.join(line for line in log.splitlines() if '[Warning]' in line)+'\n')
    if result.returncode or '[Critical]' in log:
        (CACHE/'last_cli_error.txt').write_text(log,encoding='utf-8')
        raise RuntimeError(f'PureRef CLI {result.returncode}: '+log[-1800:])
    return log


def build(nodes, resume_batch=0):
    """分批原生导入，避免 Windows 命令行长度上限；候选保存原路径以兼容2.1.3。"""
    candidate=CACHE/'drop_board_candidate.pur'
    if candidate.exists() and not resume_batch:
        raise FileExistsError('候选已存在，请先审查，避免覆盖未知修改: '+str(candidate))
    batches=[]; batch=[]; chars=600
    for node in nodes:
        command=f'load;{node["path"].replace(",",",,")};{round(node["x"])};{round(node["y"])}'
        if chars+len(command)+8>26000:
            batches.append(batch); batch=[]; chars=600
        batch.append(command); chars+=len(command)+8
    if batch: batches.append(batch)
    for i,batch in enumerate(batches):
        if i < resume_batch:
            continue
        # 对已打开 .pur 使用同一路径保存；另一路径在2.1.3会报无法打开。
        commands=([f'load;{candidate}'] if i else [])+batch+[f'save;{candidate}','exit']
        run_cli(commands,timeout=240)
        if not candidate.exists(): raise RuntimeError('未生成候选')
        print(f'BATCH {i+1}/{len(batches)} | {candidate.stat().st_size/1e6:.1f} MB',flush=True)
    run_cli([f'load;{candidate}',f'exportScene;{OUT}/overview.png;3200;5200;true;false;true','exit'])
    return candidate


def index_html(records, groups):
    """生成可检索的来源索引；图片链接指向原文件，避免复制参考库。"""
    parts=['<!doctype html><meta charset="utf-8"><title>dro:p 参考资料索引</title>',
           '<style>body{background:#202426;color:#eef0ed;font:16px Microsoft YaHei,sans-serif;margin:40px}a{color:#9dd6d1}input{padding:12px;width:70%;margin:20px 0}article{padding:15px;border-top:1px solid #465053}small{color:#adb7b4}summary{cursor:pointer}h2{color:#b9d5b7}</style>',
           '<h1>dro:p · 参考资料总板</h1><p>2026-09-28 · 本地研究资料。版权归原作者，不作为项目贴图或可再分发素材。</p>',
           f'<p>{len(records)} 张独立参考 · <a href="drop_all_references.pur">打开 PureRef</a> · <a href="overview.png">总览</a> · <a href="manifest.json">完整清单</a></p>',
           '<input placeholder="搜索编号、文件名、作者、分组或出处" oninput="document.querySelectorAll(\'article\').forEach(e=>e.hidden=!e.textContent.toLowerCase().includes(this.value.toLowerCase()))">']
    for group in groups:
        parts.append(f'<h2>{html.escape(group["title"])} · {group["count"]} 张</h2>')
        for rec in records:
            if (rec['section'],rec['group'])!=(group['section'],group['group']): continue
            parts.append(f'<article><b>{rec["id"]} · {html.escape(Path(rec["path"]).name)}</b> <small>{rec["size"][0]} × {rec["size"][1]}</small>')
            for alias in rec['originals']:
                parts.append(f'<p><a href="../../{html.escape(alias["path"])}">{html.escape(alias["path"])}</a></p>')
                if alias['provenance']:
                    parts.append('<details><summary>来源与用途</summary><pre style="white-space:pre-wrap">'+html.escape(json.dumps(alias['provenance'],ensure_ascii=False,indent=2))+'</pre></details>')
            parts.append('</article>')
    (OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')


def main():
    """准备清单/排版；带 --build 时实际生成候选，最终发布在验证之后。"""
    parser=argparse.ArgumentParser(); parser.add_argument('--build',action='store_true')
    parser.add_argument('--resume-batch',type=int,default=0); args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); (CACHE/'labels').mkdir(parents=True,exist_ok=True)
    paths,records=inventory(); nodes,groups,size=arrange(records)
    manifest={'date':'2026-09-28','reference_files':len(paths),'unique_images':len(records),
              'duplicates_merged':len(paths)-len(records),'nodes':len(nodes),'board_size':size,'group_count':len(groups),'groups':groups,'images':records,
              'scope':'Existing Shot_Test art references and original-film analyses; generated WIP renders, production textures, UI screenshots excluded.',
              'rights':'Original authors retain rights; local reference study only.',
              'cli_documentation':'https://www.pureref.com/handbook/automation/'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (CACHE/'layout.json').write_text(json.dumps(nodes,ensure_ascii=False,indent=2),encoding='utf-8')
    index_html(records,groups)
    print(json.dumps({k:manifest[k] for k in ['reference_files','unique_images','duplicates_merged','nodes','board_size']},ensure_ascii=False),flush=True)
    if args.build:
        print('CANDIDATE '+str(build(nodes,args.resume_batch)),flush=True)


if __name__=='__main__':
    main()
