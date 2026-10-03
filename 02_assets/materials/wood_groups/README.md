# 三组木材编辑入口

1. `school_board.sbs`：课桌、椅子与讲台的清漆木板。`GrainContrast` 控制 CC0 扫描木纤维与程序木纹的混合。PlywoodColor 输入使用 `../../textures/polyhaven/plywood/4k/plywood_diff_4k.jpg`；在 Designer 中将该图片接入此输入即可按完整配方预览。批处理渲染通过 manifest 中的 `--set-entry` 命令提供同一输入。
2. 黑板木框保留在 Blender 的 `Wood / 02 Blackboard inherited desk finish` 组中，沿用修改前椅子的完整木材网络，没有重新生成另一套近似贴图。粉笔灰在各资产材质中叠加。
3. `cabinet_wood.sbs`：书架、柜体的独立程序长纹。`GrainContrast` 控制木纹与棕色底漆之间的对比。

原生 SD 节点保留默认名称，用独立注释说明加工步骤。输出到 `../../textures/generated/wood_groups`，每组 6 张 4096×4096 贴图，周期 0.6 m。正片使用颜色、粗糙度及 OpenGL 法线；Height/Grain/ScratchMask 同时留作后续编辑。

旧漆磨损继续使用资产自己的边缘/接触网络，与新木纹组合，避免把所有资产烘成同一张磨损图。所有修改的持久入口是 `../../work/classroom_props.blend`，发布库为 `../../library/classroom_assets.blend`。

实物照片为参考研究，未进入贴图；唯一扫描输入为既有 Poly Haven plywood（CC0）。完整命令、seed、分辨率、图像哈希见 generated/wood_groups/manifest.json。
