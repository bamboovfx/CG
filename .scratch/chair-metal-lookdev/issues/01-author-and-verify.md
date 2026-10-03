# 制作椅子金属工艺层与表现层

State: done
Status: ready-for-human
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-10-01

## Acceptance

- [x] 原生SD源／SBSAR与高精度通道可编辑且可渲染。
- [x] 11个涂漆金属部件分层制作，钢材／漆／锈的Metallic正确；12个螺钉采用独立深色工艺变体。
- [x] 参考特定损伤位置；掉漆、锈蚀、老化、划痕和脏渍独立控制。
- [x] 保留木材、原几何／UV／法线、胶脚和用户编辑。
- [x] 同光分层、近景与归零检查；工程重开通过并应用到当前文件。
- [x] 用户通过视觉效果。

## Evidence

- [回归原参考的最新调色](../../../06_review/chair_metal_reference_color_20261001/report.md)、[当前整椅](../../../06_review/chair_metal_reference_color_20261001/whole.png)、[当前横管近景](../../../06_review/chair_metal_reference_color_20261001/rail.png)。

- [上一轮整体灰褐老化调色（用户认为过重）](../../../06_review/chair_metal_age_color_20261001/report.md)、[上一轮整体图](../../../06_review/chair_metal_age_color_20261001/after_whole.png)、[上一轮横管近景](../../../06_review/chair_metal_age_color_20261001/after_rail.png)。

- [制作与验证报告](../../../06_review/chair_metal_layers_20261001/report.md)、[整椅对比](../../../06_review/chair_metal_layers_20261001/whole_comparison.jpg)、[横管分层对比](../../../06_review/chair_metal_layers_20261001/rail_comparison.jpg)、[真实100%裁片](../../../06_review/chair_metal_layers_20261001/map_100_percent.png)。
- [当前工作文件](../../../02_assets/work/school_chair.blend)、[原生SD](../../../02_assets/materials/chair_metal_layers/chair_metal_layers.sbs)。

## Comments

- 2026-10-01：用户认为整面褐色过重，要求以原课椅照片为准。重新核对参考：大面积是灰白旧漆，褐色主要是局部损伤／近地锈蚀。减弱全局老化覆盖并中和色相，保留既有局部损伤；候选同光检查后更新当前文件。

- 2026-10-01：用户要求将整体偏白金属改为氧化灰褐色。重开调色，保留工艺底层，增加Age驱动的全表面变色与局部变化；先验证候选，同光渲染后应用实时工程。

- 2026-10-01：读取实时Blender，当前文件为木材清理后工程，11个漆面部件共用旧Baked Paint PBR。按用户参考区分工艺／表现；高精度内容与米制资产位置分开，先完成可审阅候选。

- 2026-10-01：完成77节点原生Designer配方和21张4K通道，以CC0 Rust Coarse 01原始8K辅助锈微细内容。11个漆面件与12个深色螺钉分别绑定本地坐标，显式三向投射解决旋转坐标错位，不重展UV。参考位置安排长条间断剥漆、连接与近地锈蚀，五个表现强度独立。整椅／横管／连接／背面固定三点光64spp验证；Blender归零与直接工艺输出最大差1个8位值；原生SD4K六个最终通道归零与工艺最大差全为0、六个相关蒙版全0。候选和当前工作文件重开54项通过，已追加到实时工作文件并原位保存，木材／全部几何UV法线／胶脚／当前用户编辑保护检查通过。技术完成，视觉进入review。

- 2026-10-01：按最新要求完成整体灰褐老化修订。共享表现组增加Age Color／Age Coverage／Age Variation，11个漆面件Age=0.95，颜色#796957；保留干净工艺与原损伤细节。同光前后和横管近景已检查并应用当前实时工程；独立重开原54项检查及新参数接线通过。原生SD和贴图未更改，本轮调色权威为当前Blender表现组。继续review，待用户确认视觉效果。

- 2026-10-01：上一轮整面褐色被退回后，重新对照原照片，将11件漆面调整为中性灰白旧漆：Age=0.80，Age Color=#96988F，Age Coverage=0.30，Age Variation=0.40。原局部褐色锈蚀／掉漆节点保持，工艺层与木材未改。同光整椅和横管近景已查看并原位保存当前工程，独立重开54项及11件参数检查通过。继续review。

- 2026-10-01：用户确认“这个凳子工作流基本通过”，授权将当前整椅替换到原场景；当前Lookdev验收通过。
