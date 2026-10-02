"""为本轮窗户修正生成本地参考清单与可审阅网页；原图仅供研究，不作为贴图。"""
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
REF=ROOT/'01_preproduction/references/window_hardware_20260927'
OUT=ROOT/'06_review/window_hardware_correction'
sources=[
    {'file':'crescent_HHJ0895.jpg','url':'https://parts.ykkap.co.jp/img/goods/L/PS_200YSHHJ-0895.jpg',
     'page':'https://parts.ykkap.co.jp/shop/g/gYKHHW-HHJ-0895/',
     'use':'底座23.3×66mm，孔距40mm，扁平拨柄与杯状锁片轮廓。'},
    {'file':'pull_HHK12630.jpg','url':'https://parts.ykkap.co.jp/img/goods/L/PS_200HHK12630.jpg',
     'page':'https://parts.ykkap.co.jp/shop/g/gCHHHW-HHK12630/',
     'use':'拉手外边26×134mm，凹槽16×105mm；薄边嵌入式结构。'},
    {'file':'installation_HHW11-050.pdf','url':'https://parts.ykkap.co.jp/download/HHW11-050.pdf',
     'page':'https://parts.ykkap.co.jp/download/HHW11-050.pdf',
     'use':'已看第3、8、9页：锁柄/锁杯共同转动，内窗锁体、外窗扣座的安装关系。'},
    {'file':'section_E16191006.pdf','url':'https://cad.ykkap.co.jp/downloads/file/housing/pdf/E16191006.pdf',
     'page':'https://cad.ykkap.co.jp/downloads/file/housing/pdf/E16191006.pdf',
     'use':'核对双轨、交接窗梃及侧装月牙锁的空间关系；现代窗型不作为原片型号证据。'},
]
for s in sources:
    s.update(accessed='2026-09-27',owner='YKK AP',license='版权归来源厂商；本地研究参考，未获商业再分发或贴图授权',
             sha256=hashlib.sha256((REF/s['file']).read_bytes()).hexdigest())
(REF/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
# 页面直接展示真实渲染和厂商原图，不生成或修饰参考照片。
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>窗户五金 · 硬表面修正</title>
<style>body{background:#171d22;color:#e4e7e9;font:16px/1.75 "Microsoft YaHei",sans-serif;margin:0}main{max-width:1400px;margin:auto;padding:36px}a{color:#98c8ea}h1{font-size:30px}h2{font-size:22px;margin-top:35px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}figure{margin:0}img{width:100%;background:#303942}figcaption{padding:10px 0;color:#bac8d0}.refs img{width:200px;height:200px;object-fit:contain;background:white}.notice{background:#23313a;padding:18px}small{color:#a6b7c1}@media(max-width:750px){.grid{grid-template-columns:1fr}}</style>
<main><h1>外窗五金修正</h1><p>2026-09-27 · 六组月牙锁 / 十二处凹入拉手 · 按硬表面流程分件、开槽、倒角与验证</p>
<p class="notice">本轮依据厂商零件图修正可见结构。锁体、扣座的安装偏移为既有52mm轨距适配；这不是原片指定品牌或经过工业配合认证的产品复刻。</p>
<h2>同机位对比</h2><div class="grid"><figure><a href="before_closed.png"><img src="before_closed.png"></a><figcaption>修改前：圆管弯环、突出方块拉手，锁体朝向不合理。</figcaption></figure>
<figure><a href="after_closed.png"><img src="after_closed.png"></a><figcaption>修改后：侧面安装、封闭锁杯、扁平拨柄、扣座及真实凹槽。</figcaption></figure></div>
<h2>当前开窗状态</h2><a href="after_open.png"><img style="max-width:900px" src="after_open.png"></a><p>保留控制器Y约−0.217m；对应月牙锁已转到解锁状态。评审图使用中性灯光，未改正式镜头灯光。</p>
<h2>可继续编辑</h2><ul><li><code>ctrl_window_left_04</code>：Y方向推拉，Y=0为关闭位置。</li><li><code>ctrl_window_lock_02</code>：Y旋转0°为闭锁、180°为解锁，拨柄与锁杯一起转动。</li><li>十二根窗梃保留 Boolean → Bevel → Weighted Normal；CUT pull pocket 切割体默认隐藏，随所属窗梃移动。</li><li>先将锁解开，再滑动窗扇；本轮没有添加开窗动画。</li></ul>
<h2>本次实际采用的参考</h2><div class="grid refs"><figure><a href="../../01_preproduction/references/window_hardware_20260927/crescent_HHJ0895.jpg"><img src="../../01_preproduction/references/window_hardware_20260927/crescent_HHJ0895.jpg"></a><figcaption><a href="https://parts.ykkap.co.jp/shop/g/gYKHHW-HHJ-0895/">YKK AP HHJ-0895</a>：底座、40mm孔距和拨柄轮廓。</figcaption></figure>
<figure><a href="../../01_preproduction/references/window_hardware_20260927/pull_HHK12630.jpg"><img src="../../01_preproduction/references/window_hardware_20260927/pull_HHK12630.jpg"></a><figcaption><a href="https://parts.ykkap.co.jp/shop/g/gCHHHW-HHK12630/">YKK AP HHK12630</a>：嵌入式拉手的外框与内槽尺寸。</figcaption></figure></div>
<p><a href="../../01_preproduction/references/window_hardware_20260927/installation_page_09.png">安装/扣合图（第9页）</a> · <a href="../../01_preproduction/references/window_hardware_20260927/section.png">双轨剖面图</a> · <a href="../../01_preproduction/references/window_hardware_20260927/sources.json">来源、用途、许可与SHA256</a></p>
<p><a href="report.md">修改范围与验证记录</a> · <a href="published_validation.json">正式应用记录</a> · <a href="reopened_published.json">保存重开检查</a></p><small>厂商图片仅用于本地研究，版权归YKK AP；没有将图片当作场景贴图。艺术效果待用户评审。</small></main></html>'''
(OUT/'index.html').write_text(page,encoding='utf-8')
print('Reference manifest and review page written')
