# 修复胶脚分件并记录逐环节制作流程

State: done
Status: ready-for-human
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-10-01

## Acceptance

- [x] 检查底部四个胶脚；优先在现有模型中分件，必要时才重新生成。
- [x] 胶脚独立对象／集合／材质，可分别编辑；现有形状、UV和自定义法线保持。
- [x] 复用木材、漆面和胶脚已有材质，保存到用户当前工程并重开检查。
- [x] 同光近景验证分件边界与四个胶脚的材质。
- [x] 记录模型参考→imagegen多视图→Tripo智能拓扑／分件／UV→工艺与表现材质→Blender验证及逐级返修规则。
- [x] 用户通过视觉效果。

## Evidence

- [当前规格](../spec.md)。
- [分件报告](../../../06_review/chair_foot_caps_20261001/report.md)、[底部近景](../../../06_review/chair_foot_caps_20261001/feet.png)、[重开检查](../../../06_review/chair_foot_caps_20261001/reopen_validation.json)、[完整制作流程](../../../docs/workflows/reference_to_material_asset.md)。

## Comments

- 2026-10-01：用户回复“ok”并继续要求制作脚部材质，分件环节通过，进入材质环节。

- 2026-10-01：实时文件有用户未保存编辑。确认LP_part_00为独立胶脚，另外三个胶脚连在LP_part_01／LP_part_13钢管内；三个交界均为16边闭环，可沿既有面分离，不需要重生成。

- 2026-10-01：三个胶脚沿原面分出，四个胶脚独立对象／独立材质并归入CHAIR / Foot caps。源面并集无丢失、坐标和两套UV变化0，自定义法线转移后最大编码误差约0.02021°。复用既有胶脚材质，木材、钢管材质和用户未保存编辑保留，原位保存当前文件，重开30项检查通过。完整记录逐环节检查与返修／复用策略。技术完成，进入review。
