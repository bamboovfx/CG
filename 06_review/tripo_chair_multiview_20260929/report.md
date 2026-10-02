# Tripo Studio 教室椅四视图样件复测（2026-09-29）

## 结论

Studio 四视图 → P2.0「干净拓扑」→ FBX → Blender UV → Substance 3D Painter → 2K PBR → Blender 已实际跑通，可作为流程候选。当前视觉和网格质量未达到项目的次世代硬表面资产标准；不发布到主教室镜头。

本轮停止 API 路线。Studio 生成扣 100 Studio 积分；没有提交 API 生成调用。DCC Bridge 未安装或实测，本轮以 Studio 导出 FBX 和 Blender 手动导入完成传输。

## 输入与操作

- 原始教室椅来源：`02_assets/work/classroom_props.blend` 中的已建高模。由该模型渲染 `chair_front.png`、`chair_left.png`、`chair_right.png`、`chair_back.png` 四张正交视图，作为 Studio 输入；这是一项重建保真度测试，并非从实拍照片独立创作新造型。
- [Studio 任务](https://studio.tripo3d.ai/zh/workspace/generate/6864e057-716e-4bfd-a739-8ca41eb1e812)：四图输入、Smart Mesh P2.0、Quad、目标 10,000 面。导出 `tripo_chair_multiview_p2_quad_10000.fbx`。
- Blender 5.1.2：保留隐藏的原始导入；复制出 26 个可选部件，按原样件高度缩放到 0.8045 m，Smart UV 投射为一张 0–1 图集；渲染泥模与棋盘格检查。UV 是自动展开，未人工指定结构接缝或统一纹理密度。
- Painter 12.1.4：导入 UV 后 FBX，建立 2048×2048 纹理集；完成 7 项自身网格烘焙图（Normal、World Space Normal、ID、AO、Curvature、Position、Thickness）。使用可编辑的油漆钢与木材层，导出 7 张贴图。这是自身网格烘焙，**不是高模到低模细节烘焙**。
- Blender：Base Color 以 sRGB 接入；Metalness、Roughness、OpenGL Normal 以 Non-Color 接入；AO 独立保留，不乘进 Base Color；Height 归档且不驱动位移。六张实际使用或归档的贴图已打包入独立 `.blend`。

## 客观检查

| 项目 | 结果 |
|---|---|
| Tripo FBX | 9,226 顶点、9,392 面：8,329 四边形、1,063 三角形；26 个连通件 |
| 网格缺陷 | 688 条边界边、5 条非流形边；导出 FBX 无 UV |
| 候选尺寸 | 0.4366 × 0.4563 × 0.8045 m，基于原样件高度校准 |
| Blender UV | 26 部件均有 UV；棋盘格读回可见管件拉伸与方向跳变，尚未做岛间距/密度/重叠的数值验收 |
| Painter → Blender | 7 张 2K PNG 已导出；材质节点读回、Cycles 中性光渲染成功 |
| 镜头读回 | 未做；正式镜头工程未修改 |

视觉问题：椅子大轮廓可辨，但金属圆管和接头处有生成痕迹，木面纹理呈噪点状且缺少合乎板材方向的纹理组织；局部细节和实际制造结构仍须手工复核。UV 格图和材质图只能说明链路工作，不能说明资产已可进镜头。

## 文件与追溯

所有候选位于 `07_pipeline/cache/tripo_chair_multiview_20260929/`：

- 四视图：`chair_front.png`、`chair_left.png`、`chair_right.png`、`chair_back.png`，以及 `chair_fourview_source.blend`。
- Tripo 原始导出：`tripo_chair_multiview_p2_quad_10000.fbx`；审计 `fbx_audit.json`。
- Blender UV 候选：`tripo_chair_blender_candidate.blend`；Painter 输入 `tripo_chair_painter_input.fbx`；审计 `candidate_audit.json`；预览 `candidate_clay.png`、`candidate_uv_grid.png`。
- Painter 工程：`tripo_chair_multiview_p2_20260929.spp`；导出贴图位于 `textures/`。
- Blender PBR 候选：`tripo_chair_pbr_candidate.blend`；渲染 `candidate_pbr.png`；审计 `pbr_audit.json`。
- 复现脚本：`render_four_views.py`、`prepare_blender_candidate.py`、`apply_painter_textures.py` 等。

主要 SHA256：原始 `classroom_props.blend` `65e545219296e94f9b97b2e8c1755fd7b6e0575ee23cda4a94d7902b2fe78160`；Tripo FBX `5380b60aa696efd8b9765b94a77baac0cc84c9998f6ee58940c36eacec31551d`；Painter SPP `d24e30430a820e3e693679579883a0b697620b32a1ab832a870c47d6ae1ea7ee`；最终候选 BLEND `1580bbb6b6476cea6bd51066a4955bc5b4c2e675be58e454823b51b050bb2b02`。

## 下一阶段的质量门槛

1. 参照实物和原样件，修复圆管、靠背固定件、板材厚度、承力连接与非流形部位；明确可编辑高模和保轮廓低模。
2. 低模先定型倒角、硬边与三角化，再按结构布置 UV 接缝，测量岛间距、纹理密度与重叠。
3. 以配对高低模执行 OpenGL 法线和独立 AO 烘焙，逐个检查薄板背面、螺孔、接缝与投射漏点。
4. 按工艺重做木板纹理方向、涂装边缘磨损和金属接触处粗糙度；在原教室灯光和主机位进行近景及运动检查，再决定是否替换镜头资产。

## DCC Bridge 的边界

按 [Tripo 官方 Blender Bridge 说明](https://www.tripo3d.ai/integrations/blender)，Bridge 是 Studio 到 Blender 的传输插件：在 Studio 的 Export 中选择 Send To Blender，模型和贴图直接进入打开的 Blender 场景，省去手动下载与导入。它不负责人工曲面建模、布线、生产级 UV、高低模烘焙或材质美术判断。官方当前说明 Blender 4.1+，Studio Pro/Max/Team 可用；本轮没有验证当前账号的 Bridge 权限。

## 参考复核与材质修订（同日）

再次对照 `01_preproduction/references/props/20160220_201e63.JPG`、`20160220_47c158.JPG`、`props_01.jpg` 和既有课椅评审 `06_review/chair_reference/full.png`、`back_detail.png`。实物的座板是暖蜜色清漆，木纹沿板宽连续流动；靠背木板的纹理更细、更平直。钢管是旧象牙色漆，深色掉漆是稀疏的局部小块，紧固件偏冷银色，脚套偏黄且更哑。初版 Painter 木面呈深色斑点噪声，管架表面的白色/深色磨损分布过密，且金属度贴图没有稳定地区分漆膜和露钢。

已另存材质修订候选：`07_pipeline/cache/tripo_chair_multiview_20260929/tripo_chair_reference_mat_candidate.blend`。木板使用项目现有 Substance Designer `school_board` 的 4K BaseColor、Roughness、Height、ScratchMask；按分件局部坐标把纹理分别定向到座板和靠背，图案周期 0.6 m。清漆保持非金属，粗糙度约 0.29–0.43，微凹凸和擦痕独立控制。钢架保留 Painter 图集作为轻度旧化依据，主体改为非金属象牙色漆，局部弯管及横撑采用较多的稀疏露钢小斑；螺钉改冷色金属，脚套改哑光旧象牙色。贴图随物体移动，不依赖场景世界坐标。复核了网格的**世界**包围盒，候选本身已是 Blender Z-up，高度 0.8045 m；分件局部轴有旋转，不能用 `Object.dimensions` 直接判断世界方向。

- [材质修订整体预览](../../07_pipeline/cache/tripo_chair_multiview_20260929/candidate_reference_mat.png)
- [座板、靠背和管架近景](../../07_pipeline/cache/tripo_chair_multiview_20260929/candidate_reference_mat_detail.png)
- [材质修订审计](../../07_pipeline/cache/tripo_chair_multiview_20260929/reference_mat_audit.json)
- 可复现脚本：`07_pipeline/cache/tripo_chair_multiview_20260929/refine_reference_materials.py`。

修订版 `.blend` 已用 Blender 5.1.2 的 Cycles 完成整体和 1600×1600 近景渲染，四张 Designer 图与 Painter 基础贴图已打包。该文件 SHA256 为 `4d61a5001354c215ee0227ef894cf9bddd3bc4f470621dc1ef19b743e9a25764`。这是材质外观候选，没有回写 Painter `.spp` 或重新导出游戏用 PBR 图集。木板边缘的层压结构、实物特有的宽幅木纹和局部划痕仍只能近似；Tripo 管件的悬空端、连接与拓扑缺陷依然存在，当前不满足正式资产验收门槛。正式镜头与原资产源工程未修改。

还测试过直接把原椅的 `Wood / 01 School board / chair / Surface / Desk family lightly worn wood` 材质附到 Tripo 木板上；[测试图](../../07_pipeline/cache/tripo_chair_multiview_20260929/source_wood_test.png)变成近乎纯色，因为该材质依赖原资产的坐标与遮罩组织，不能直接移植。因此保留按 Tripo 分件坐标重建的 Designer 木材材质。
