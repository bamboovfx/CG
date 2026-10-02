# 椅子金属整体灰褐老化调色 — 2026-10-01

此版本整面褐色被用户认为过重，已由[回归原参考的灰白旧漆版本](../chair_metal_reference_color_20261001/report.md)取代；下文保留当轮制作记录。

用户指出金属整体偏白，要求氧化后呈褐色。已将11个涂漆部件改为整面灰褐老化，并原位保存到[当前工程](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)。

保持干净工艺层，调色在共享表现层内完成。新增默认名称的Math节点，用注释框解释整面覆盖与4K局部变化。Age Color为sRGB `#796957`，Age Coverage为0.78，Age Variation为0.30，11个漆面件Age为0.95。颜色因子为Age驱动的整面覆盖加原局部老化变化，并限制在0–1。Age=0时新颜色路径的混合因子为0；本轮未重新渲染全部表现归零对照。

原有掉漆、深褐氧化、赭色局部锈、钢灰露底、划痕和脏渍路径保留。增加Age也会通过既有路径增强老化粗糙度和涂层雾化。深色螺钉仍使用原Age=0.05，受共享新颜色路径的影响很弱。木材、干净工艺组、网格／UV／法线、物体位置、胶脚、灯光、色彩管理与用户机位保护检查通过。

同一三点灯光、固定种子101、64spp、透视机位渲染实际前后图和上横管近景。保存后用独立Blender进程重开：原54项保护／依赖／接线检查通过，新老化控制接线和11件参数亦通过：[重开检查](reopen_validation.json)、[应用记录](applied.json)。视觉状态仍待用户评审。

![调色前](before_whole.png)

![调色后](after_whole.png)

![上横管近景](after_rail.png)

本轮是Blender表现层参数与接线修订，原生Designer配方和导出贴图未改；当前Blender节点组为本轮调色权威。[修改脚本](../../07_pipeline/scripts/revise_chair_metal_age_color.py)只调整老化颜色，不重建材质。恢复副本：`07_pipeline/cache/chair_metal_age_color_20261001/pre_color.blend`。独立候选：同目录`age_color_candidate.blend`。

恢复副本SHA256：`7b64c1be3849d35c1725536d295318eba8c61a2a06a6287bda5095e2c44ec248`。保存的当前文件SHA256：`acf1b592ac6f4ad86a8fdb45bcece6da7a1c46604412addbe2c0b34e919ccecf`。
