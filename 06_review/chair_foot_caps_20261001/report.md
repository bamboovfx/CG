# 课椅底部胶脚分件修复 — 2026-10-01

已在现有网格上分出四个独立胶脚，并保存到[当前工作文件](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)。不需要imagegen或Tripo重生成，本次在模型分件环节解决问题。

原状：只有前左胶脚LP_part_00独立；后左连在LP_part_01内，前右和后右连在LP_part_13内。三个交界都有16边闭环。沿已有面分离，没有切新面、删面或改变形状。

| 胶脚 | 对象 | 面数 | 材质 |
|---|---|---:|---|
| 前左 | LP_part_00 | 484 | AITA yellowed matte foot caps |
| 后左 | Foot cap / rear left | 552 | Chair foot caps / rear left |
| 前右 | Foot cap / front right | 540 | Chair foot caps / front right |
| 后右 | Foot cap / rear right | 532 | Chair foot caps / rear right |

四件位于原集合下的新子集合`CHAIR / Foot caps`，各有独立网格和材质。三个新胶脚复制已有胶脚材质根树，复用原黄白哑光外观，可以分别调整。钢管保留原物体及本地材质坐标绑定，木材和金属工艺／表现树没有重做。

逐源面检查分离后的面并集：没有丢面或重复面，顶点坐标和UVMap／UV_Material两套UV的最大变化为0。转移原角点法线后，Blender16位相对基底重新编码产生最大约0.02021°夹角误差，没有明显反光接缝。保留原形状、原UV，不代表本轮重新展开或提升了原UV纹理密度。

实时场景初始有未保存编辑，已完整备份再用于候选验证；实际应用前又保存最新实时备份。保护检查包括其它几何、原材质组、木材、原胶脚、物体变换和Plane活动选择；保存后的独立重开30项检查通过，包括全部结果几何／UV／法线、四个独立胶脚、四个独立材质、实际赋材质、打包图像和临时标记清除。[候选记录](candidate.json)、[应用记录](applied.json)、[重开检查](reopen_validation.json)。旧的“全部原网格摘要相同”检查不适用于本轮两个网格的有意分件，以上源面并集和重开摘要为本轮检查依据。

重开时两个零用户、未设置Fake User的历史材质`AITA dark fastener heads`／`Baked Paint PBR`未保留，这是Blender保存规则；实际使用的所有材质均通过检查。没有通过删除有效材质绕过检查。

同光64spp／种子101底部透视近景：

![四个胶脚](feet.png)

当前文件SHA256：`7190b74dd17d70ad4200108e4667813ee1b98a0031be87845f5ab8bfde5294b4`。恢复副本和候选在`07_pipeline/cache/chair_foot_caps_20261001/`：`pre_split_live.blend`、`pre_apply_live.blend`、`foot_caps_candidate.blend`。脚本：[分件](../../07_pipeline/scripts/separate_chair_foot_caps.py)、[重开检查](../../07_pipeline/scripts/verify_chair_foot_caps.py)。

完整的参考→imagegen多视图→Tripo拓扑／分件／UV→工艺／表现材质→Blender验证及逐级返修规则，已记录在[参考制作流程](../../docs/workflows/reference_to_material_asset.md)。技术完成，视觉效果待用户确认。
