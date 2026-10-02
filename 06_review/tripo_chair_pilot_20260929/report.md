# Tripo → Blender → Substance Painter 教室椅子样件验证

日期：2026-09-29。范围：独立候选，未写入 `sq010/sh010` 工作镜头。样件由当前 Tripo 账号生成，用于验证工具链；该生成资产的对外分发和商业使用条款未在本次核定。

## 结论

- **链路连通**：Tripo Studio 可登录、生成 H3.1 高模、Smart Mesh 重拓扑、导出 GLB；Blender 5.1.2 可导入；Substance 3D Painter 12.1.4 可导入低模/高模、完成 7 项 mesh map 烘焙、接入颜色/金属度/粗糙度并导出 glTF PBR；导出的 GLB 可在 Blender 中读回和渲染。
- **资产未达到本项目次世代道具关口**：自动低模的 UV 极碎，高低模都是单网格/单材质，钢管和装配局部有形变，烘焙预览有射线黑斑。现有导出只能作为概念和可修复的候选，不能直接取代镜头工作工程中的椅子。
- **视觉状态**：中性光单帧供评审，尚未做棋盘格/密度量测、材质分件重建、同光前后对照、镜头原光及动态读回。因此不能标为视觉通过或发布。

![Painter 导出 GLB 在 Blender 中的中性光预览](preview.png)

## 输入与步骤

1. Tripo H3.1 文生模型：1970 年代教室独立椅子，弯管涂装钢架、弧形胶合板座面与靠背、支架/螺栓/脚垫；完整单件、无桌子/人物/背景。开启 Ultra Geometry、纹理、8K、PBR、去光照；三角面上限 2M。生成用 65 credits。高模统计：约 1,909,692 三角面、978,910 顶点。
2. Tripo Smart Mesh P1.0，目标 10,000 四边面，花费 40 credits；网页显示结果 8,990 quads / 8,583 vertices。FBX 的签名 ZIP 链接在 Chrome 中被 `ERR_BLOCKED_BY_CLIENT` 拦截，本次改用成功下载的 GLB。导出后 Blender 读回是三角面：17,160 三角面、13,330 split 顶点、1 个 UV、1 个材质；约 0.580 × 0.592 × 0.978 m。不能把网页显示的四边面状态等同于本次 GLB 的可编辑低模。
3. 独立 Blender 后台进程将高低 GLB 转成 FBX。Painter 新建 2K OpenPBR 工程，以低模为目标、高模为烘焙源；Bake Mesh Maps 的 Normal、World Space Normal、ID、AO、Curvature、Position、Thickness 全部完成。
4. 从低模 GLB 原样提取 8K Base Color 和 4K glTF RM，按 **G=Roughness、B=Metallic** 拆出灰度图，在 Painter 的 Fill Layer 接入 Base Color、Base Metalness、Specular Roughness。当前 Painter 工程保存了烘焙和可编辑贴图槽；尚未完成针对木材/涂层/裸钢/橡胶的重新分层制作。
5. Painter 使用 **glTF PBR Metal Roughness** 模板导出 2048² PNG：Base Color、Normal、Occlusion/Roughness/Metallic 打包图，以及 GLB/GLTF。Blender 重新导入导出 GLB，几何尺寸保持一致并完成独立预览渲染。ORM 图像的 RGB 通道均有非空数据；法线图 B 通道约 96% 像素接近 255。

## 质量问题与判断

| 项目 | 观察 | 对次世代流程的影响 |
|---|---|---|
| 结构/轮廓 | 椅子整体可识别；钢管截面、支腿与连接处不匀，部分零件似乎直接融合 | 不能用纹理修补装配几何；需要按实物尺寸重建承力结构、倒角和连接件 |
| 低模/UV | 1 个三角化网格、1 个材质槽，UV 大量细碎岛；木、钢、橡胶混在一张图 | 不利于统一 texel density、接缝和工艺分层，需重新分件、重拓扑和展开 |
| 烘焙 | 7 项 bake 均显示完成；Normal/AO 预览在腿和连接处有黑斑/射线伪影 | 需要匹配分件或爆炸烘焙、修法线与 cage/射线距离，再检查薄片背面 |
| PBR | 原贴图成功映射到 Painter；低模 GLB 原始法线为 JPEG；金属度图含大量中间值 | 涂装钢材/露底金属、木板清漆、橡胶脚垫须按物理层次重作；不要仅放大到 8K 期待质量提升 |
| 跨 DCC | Painter 导出 GLB 能在 Blender 渲染；中性灯下材质比 Painter 预览更浅 | 色彩管理、灯光和目标镜头高光需同光复核，不能用单一预览判定通过 |

## 建议的可执行制作链

1. Tripo 主要产出造型草案/高模参考，选中轮廓与比例后进入 Blender。当前样件不建议直接作为可编辑生产高模。
2. Blender 按胶合板、涂装钢管、五金、橡胶拆件；校正尺寸/厚度/倒角和连接方式；制作可编辑高模、保轮廓低模，先固定三角化和硬边，再做结构性 UV 与棋盘格检查。
3. Painter 用分件命名或爆炸布局重烘高低模，检查 Normal/AO 接缝和薄片。以真实材质工艺分层：胶合板纤维/清漆，涂装钢的粗糙度与局部磨损，裸露金属，脚垫橡胶；再导出 OpenGL 切线法线和独立 AO/ORM。Designer 仅在木纹、涂层等可复用程序材质需要跨道具共享时引入。
4. 回 Blender 在棋盘格、中性光、`sq010/sh010` 原灯光下做同光前后对照与近景，确认 texel density、高光、接缝和运动稳定后，另行决定是否集成工作镜头。

## 文件与溯源

所有候选源和脚本位于 [`07_pipeline/cache/tripo_chair_pilot_20260929`](../../07_pipeline/cache/tripo_chair_pilot_20260929/)。审阅预览为 [`preview.png`](preview.png)。

| 文件 | SHA-256 |
|---|---|
| `tripo_school_chair_hp_20260929.glb` | `00570CC3D28E23620843FDC36ABE5893870D3E0D6EE3288962C703E4D00A349F` |
| `tripo_school_chair_lp_glb_20260929.glb` | `A61C3C484AA48DD02C388DEC2B4CEEC34C3B4F561C8B228BC9B39162FBF5885C` |
| `tripo_chair_painter_pilot_20260929.spp` | `FBFEE4533DBA6AEDC2572BE6B992902FA69DEDA1AD7E3C33C8C16F4F9EEC5D7E` |
| `painter_export/tripo_chair_painter_pilot_20260929.glb` | `45A6A6555C6CE204D2598B98BF274404D49540BEAD40FBC4E34DD2E3FD2F3D47` |
| `preview.png` | `5341CC20596CB860C67B5A1EF0DDCE5E8F5DA03BA567CAEAFB9DA4E686791517` |

复核数据：`high_glb_report.json`、`low_glb_report.json`、`high_blender_audit.json`、`low_blender_audit.json`、`painter_export_audit.json`、`pbr_audit.json`。导出贴图和模型在 `painter_export/`。主工作镜头 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend` 未由本次实验修改。

官方参考：[Tripo 导出到 DCC](https://www.tripo3d.ai/zh/help/features/how-to-export-and-import-to-dcc-tools)、[Adobe Painter 烘焙](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/baking/baking-interface)、[Adobe Painter 导出纹理](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export)。

## 2026-09-29 补充：图片输入与 DCC Bridge

前次样件的纯文字输入只约束了材质和大类，没给椅子的比例、弯管走向和背面装配证据；这是几何失真的**可能原因之一**。但图片或多视角只能减少被遮挡面的猜测，不能保证结构分件、承力连接、可编辑布线或干净 UV。Tripo [图片输入建议](https://www.tripo3d.ai/help/features/how-to-get-better-image-to-3d-results)强调主体完整、背景简洁、漫射光，侧面/背面信息不足时用多视角。当前 [功能帮助](https://www.tripo3d.ai/help/getting-started/what-features-does-tripo-have)称多视角为 2–4 张；实际可用张数以账号中的生成界面为准。

下一轮应做**同一款椅子的受控对照**：使用同一实物或一致的设计图，至少正面、侧面、背面三张，同尺度同姿态；先 Smart Mesh 小样检查轮廓、钢管和装配，再决定是否做高精模型。2026-09-29 现场工作台的多视角槽位为前/左/右/后；Smart Mesh 可选 P2.0 四边面，当前默认 5,000 面、4 个结果时按钮显示 100 credits，尚未提交生成。比较纯文字、单图和多视角在同一机位下的轮廓、几何连通、分件、布线、UV、烘焙缺陷及修复工时。没有用户认可的同一款椅子参考图时，不应拿不同设计的图片声称“输入方式提高了质量”。

工作台还提供**智能 UV**；[官方说明](https://www.tripo3d.ai/blog/smart-uv)称可对 Tripo 模型或上传模型重新拆缝和排岛，支持不超过 80,000 三角面或 40,000 四边面，并显示 UV 利用率。它可以列为低模 UV 的第二次尝试，但仍要在棋盘格、接缝、texel density 和烘焙下验收；本次未运行，也不能把文档能力算作此椅子的已通过结果。

Tripo Studio 顶栏的 **DCC Bridge 是传输插件**：生成后通过 Export → Send To 把模型直接送入已连接的 Blender 等应用，省掉逐个下载/导入。它不负责曲面建模、手工布线、UV 整理或 Painter 材质制作。现场 Studio 面板显示 Blender、3ds Max、Unity、Unreal、Maya、Cocos、Godot、ZBrush、MetaTailor、Roblox，开关均为关闭；未看到 Substance Painter。Blender Bridge 的[官方说明](https://www.tripo3d.ai/zh/integrations/blender)要求 Blender 4.1+、支持的 Chromium 浏览器，以及 Studio Pro/Max/Team 账号；当前账号是否有权限和实际端到端连接尚未验证。另一个 [Blender API 插件](https://developers.tripo3d.ai/en/docs/plugins)可在 Blender 内提交生成任务，需要 API key，API 计费与 Studio 积分分开。
