# 金属颜色回归原课椅参考 — 2026-10-01

上一轮整面灰褐色被用户认为过重。本轮重新查看用户原课椅照片，恢复大面积灰白旧漆，褐色继续由局部掉漆、氧化和近地锈蚀表现。已原位保存[同一当前工程](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)。

仅调整11个涂漆部件的现有表现接口：Age=0.80，Age Color=sRGB #96988F，Age Coverage=0.30，Age Variation=0.40。没有增加节点或重建材质。原干净工艺层、局部损伤节点、螺钉、木材、几何／UV／法线、胶脚及用户机位保持。灯光与色彩管理没有变更。

独立候选以原三点灯光、透视机位、64spp、种子101渲染整椅及横管近景，实际查看后应用实时工程。保存后独立重开：原54项保护／依赖检查和11件实际参数检查通过。[候选记录](candidate.json)、[应用记录](applied.json)、[重开检查](reopen_validation.json)。参考接近程度仍待用户视觉评审。

![整椅](whole.png)

![横管近景](rail.png)

本轮调色权威仍为Blender表现组，原生SD和贴图未改。修改前恢复副本为`07_pipeline/cache/chair_metal_age_color_20261001/pre_reference.blend`，校正候选为同目录`reference_color_candidate.blend`。操作脚本：[calibrate_chair_metal_reference.py](../../07_pipeline/scripts/calibrate_chair_metal_reference.py)。
