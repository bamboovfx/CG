# 教室模块资产与 SD 材质交付

以下保留初次模块与SD材质的交付记录。2026-09-27核对后，Blender编辑入口统一指向现有合并源；旧分散源不再作为工作入口。完整资产链路见 [当前工程基线](../../00_admin/current_state.md)。

| 分组 | Blender 源 | 原生 SD 图 | 评审 |
|---|---|---|---|
| 建筑 / 窗帘 | [classroom_environment.blend](../work/classroom_environment.blend) | [architecture_rebuild](architecture_rebuild) | [参考与近景](../../06_review/architecture_rebuild/review_sd.md) |
| 木柜 / 设备 | [classroom_props.blend](../work/classroom_props.blend) | [equipment_rebuild](equipment_rebuild) | [参考与近景](../../06_review/equipment_rebuild/review.md) |
| 黑板 / 教学陈设 | [classroom_props.blend](../work/classroom_props.blend) | [teaching_rebuild](teaching_rebuild) | [参考与近景](../../06_review/teaching_rebuild/review.md) |
| 房间壳体 / 糖果罐 | [环境源](../work/classroom_environment.blend) / [道具源](../work/classroom_props.blend) | [shell_tin_rebuild](shell_tin_rebuild) | [参考与近景](../../06_review/shell_tin_rebuild/review.md) |

初次交付包含25个可编辑 `.sbs` 和对应实编译 `.sbsar`，后续材质在各自目录继续维护。每组保留真实SAT调用、输入/输出哈希、seed、尺寸和通道语义。Blender使用2K/4K导出图；材质族共享，避免每个物件复制一套。

完整索引：[材料交付](D:/00_projects/10_CG/Shot_Test/06_review/modular_integration/review.md)

带公开图像输入的SBS在SD内需要按各组manifest加载对应CC0源图；批量重现可用其记录的sbsrender --set-entry命令。
