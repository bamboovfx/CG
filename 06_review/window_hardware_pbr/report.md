# 窗五金：UV与次世代硬表面返工

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
