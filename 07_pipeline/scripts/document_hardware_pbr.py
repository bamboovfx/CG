"""汇总真实烘焙/验证输出，生成离线对比页与资产说明；不改写参考图片。"""
import json
import shutil
import struct
from pathlib import Path

ROOT=Path('D:/00_projects/10_CG/Shot_Test'); OUT=ROOT/'06_review/window_hardware_pbr'
TEX=ROOT/'02_assets/textures/window_hardware'
manifest=json.loads((OUT/'build_manifest.json').read_text(encoding='utf-8'))
validation=json.loads((OUT/'published_validation.json').read_text(encoding='utf-8'))
shutil.copy2(OUT/'build_manifest.json',TEX/'manifest.json')
formats={}
for path in TEX.glob('*.png'):
    head=path.read_bytes()[:29]
    formats[path.name]={'width':struct.unpack('>I',head[16:20])[0],'height':struct.unpack('>I',head[20:24])[0],'bit_depth':head[24]}
(OUT/'image_formats.json').write_text(json.dumps(formats,indent=2),encoding='utf-8')
report='''# 窗五金：UV与次世代硬表面返工

日期：2026-09-28。六组窗锁与十二处拉手的78个金属部件已写回固定建筑源；视觉待用户评审。

## 本次修复

旧模型在倒角之前用局部平面投影生成UV，倒角求值后部分UV塌陷，代表件95%分位拉伸比约2.0–2.8。旧材质同时使用强方向程序噪声与不同取样链；关闭法线后的单变量对比仍保留粗条纹，说明截图的显眼条纹主要来自粗糙度方向纹理。锁柄/锁杯当前盒式法线分支未接入最终表面，不能把它误判为该部位现象的直接原因。

本次把几何倒角纳入低模，再展开和固定三角化；烘焙后无新增改变拓扑的修改器。板件采用沿长轴的细微加工纹，锁杯/轴件采用较均匀的细哑光。这是本镜头的材质设计，并非对原片零件合金或工艺的实物鉴定。

## 高低模、UV和贴图

- 9种不同零件共享图集：低模合计4,476三角面，高模求值12,156三角面；不是全教室总面数。78个金属部件复用对应网格，12个深色螺丝槽辅助件保留原状。
- 高模保留6段倒角与法线修改器；低模2段倒角保轮廓，倒角几何已固定，烘焙补充曲面高光与微加工细节。
- UVMap为独立0–1图集，无重叠采样/越界/塌陷；统一密度约159–164 px/cm。32°分区展开，岛等比例缩放与90°旋转，间距40px、烘焙膨胀20px（4K）。
- 最终代表件UV拉伸比95%分位约1.10–1.13，最大约1.17；1表示等比例。主要面棋盘格正常，倒角局部仍有轻微投影形变，不宣称数学上的全表面零变形。
- Cycles真实高→低烘焙：切线空间OpenGL Normal、AO、BaseColor、Roughness、Metallic；按爆炸排列分离不同零件，避免相邻件串投。外扩0.9mm、最大射线距离1.8mm。
- 五张4096×4096 PNG，底色sRGB，其余Non-Color。AO独立保留，不重复乘入底色。最终材质全部直接读取UV图集，没有原先混合坐标与盒投影链。
- 2048网格对UV三角形内部采样重叠数为0；图集实际面积利用率约29.2%，优先保留倒角小岛间距。检查有栅格精度边界，不能代替近景检查。

## 文件入口

- 镜头使用源：`02_assets/work/classroom_environment.blend`。
- 可编辑高低模：`02_assets/work/window_hardware_authoring.blend`。`HIGH - editable bevels` / `LOW - triangulated UV` 两集合，默认显示低模。零件采用爆炸排列便于烘焙，原对象名记录在 source_object 自定义属性。
- 图集：`02_assets/textures/window_hardware/`；旁边manifest记录来源输入哈希、部件映射、贴图哈希。
- 最终材质：`Hardware / Satin metal baked`；默认节点名称保留，解释写在Frame。
- 恢复副本：`07_pipeline/cache/window_hardware_pbr/live_before.blend`。`source_before.blend`为旧正式源的逐字节备份，相对路径按正式源目录解释。

## 继续修改

在独立高低模源中调整HIGH集合的倒角与工艺节点。若改变轮廓/拓扑，应同步LOW、重新展开并固定三角化，再烘焙；只改高模材质可重烘焙。脚本 `07_pipeline/scripts/build_hardware_pbr.py` 的bake模式支持独立源，贴图会更新；几何改动仍需新候选验证和发布，不能只重烘焙便假定建筑源拓扑同步。

UV、法线和粗糙度检查应使用中性光和镜头原光各一次。贴图分辨率应按屏幕占比判断，不以4K本身作为质量结论。当前文件没有开展全场景重新拓扑、游戏引擎LOD或全片最终渲染。

## 验证与保护

- `published_validation.json`：正式源重开通过；目标对象的变换、父级保留，非目标对象数据引用和修改器未变。
- 保留用户最新开窗Y=-0.341201m、锁控制器Y=270°。
- `authoring_validation.json`：高低模源重开，18个对象与贴图依赖有效。
- `shot_link_check.json`：主镜头重开能读取新材质，无贴图丢失；当前1089帧，24fps，1001–1100，相机/天空两个Action保留。仅输出50%分辨率/32样本样帧，没有改写正式镜头。
- 技术通过不代表用户已确认外观；本轮未改变原先140帧镜头任务的验收状态。

## 参考

- [YKK AP HHJ-0895月牙锁](https://parts.ykkap.co.jp/shop/g/gYKHHW-HHJ-0895/)：上一轮核实底座尺寸和安装结构；[既有参考板](../window_hardware_correction/index.html)。
- [YKK AP HHK12630拉手](https://parts.ykkap.co.jp/shop/g/gCHHHW-HHK12630/)：拉手尺寸与开口关系。
- [Adobe：烘焙后法线接缝](https://experienceleague.adobe.com/en/docs/substance-3d/bakers/common-issues/seams-are-visible-after-baking-a-normal-texture)：法线精度、UV边界与渲染质量需要一起检查；本轮以棋盘格和中性高光复验。
- Blender随MCP附带的本地API文档用于核对UV展开、岛打包、Selected-to-Active烘焙接口。

所有纹理由自身高模与程序材质烘焙生成，没有使用厂商照片做贴图。
'''
(OUT/'report.md').write_text(report,encoding='utf-8')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>窗五金 · UV与PBR返工</title>
<style>body{margin:0;background:#111820;color:#e9edf2;font:16px/1.7 system-ui}main{max-width:1200px;margin:40px auto;padding:0 24px}h1{font-size:32px;margin-bottom:8px}p{color:#bccbd9}a{color:#9bc8f0}.compare{position:relative;max-width:850px;margin:auto;aspect-ratio:1}.compare img{position:absolute;width:100%;height:100%;object-fit:contain}.compare .top{clip-path:inset(0 50% 0 0)}input{width:100%;margin:16px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:0;background:#19242e;padding:14px;border-radius:8px}figure img{width:100%;display:block}figcaption{margin-top:10px}small{color:#a4b5c6}.wide{width:100%}nav{display:flex;gap:24px;flex-wrap:wrap;margin:22px 0}section{margin:38px 0}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style>
<main><h1>窗五金：UV与PBR返工</h1><p>2026-09-28 · 六组窗锁 / 十二处拉手 · 已写回建筑源，外观待评审</p>
<nav><a href="report.md">制作与验证说明</a><a href="../../02_assets/work/window_hardware_authoring.blend">可编辑高低模</a><a href="../../02_assets/textures/window_hardware/manifest.json">贴图与部件清单</a></nav>
<section><h2>相同机位与中性光</h2><p>左侧修正前，右侧修正后。拖动滑块比较粗条纹、板面和锁杯高光；单击下方图片可看原图。</p>
<div class="compare"><img src="after.png" alt="修正后"><img class="top" id="before" src="before.png" alt="修正前"></div>
<input aria-label="前后比较分界" type="range" min="0" max="100" value="50" oninput="document.getElementById('before').style.clipPath='inset(0 '+(100-this.value)+'% 0 0)'">
<small>同样的1000×1000、Cycles 48 samples、AgX。没有给修正后单独增加后期滤镜。</small></section>
<section class="grid"><figure><a href="checker.png"><img src="checker.png" alt="最终UV棋盘格"></a><figcaption>最终低模的棋盘格</figcaption><small>无塌陷、无越界；主要表面保持等比例。</small></figure>
<figure><a href="pull_after.png"><img src="pull_after.png" alt="凹入拉手近景"></a><figcaption>拉手与真实凹槽</figcaption><small>沿长轴轻微加工纹，保留槽内壁厚与倒角。</small></figure>
<figure><a href="uv_layout.svg"><img src="uv_layout.svg" alt="九种零件唯一UV图集"></a><figcaption>共享4K图集</figcaption><small>每色对应一类零件。低模4,476三角面；间距40px，烘焙膨胀20px。</small></figure>
<figure><a href="../../02_assets/textures/window_hardware/Normal.png"><img src="../../02_assets/textures/window_hardware/Normal.png" alt="真实高低模烘焙法线"></a><figcaption>OpenGL切线空间法线</figcaption><small>由6段倒角高模烘焙到2段倒角低模，微加工纹理同时烘入。</small></figure></section>
<section><h2>当前镜头读回检查</h2><a href="shot_context.png"><img class="wide" src="shot_context.png" alt="当前1089帧样帧"></a><p>沿用用户当前相机、天空动画和24fps设置；这张只验证链接与镜头上下文，不代表完成了整条动态镜头。</p></section>
<nav><a href="published_validation.json">正式源验证</a><a href="authoring_validation.json">高低模源验证</a><a href="shot_link_check.json">镜头链接检查</a><a href="../window_hardware_correction/index.html">厂商参考与装配来源</a></nav></main></html>'''
(OUT/'index.html').write_text(html,encoding='utf-8')
print(json.dumps({'page':str(OUT/'index.html'),'formats':formats},ensure_ascii=False))
