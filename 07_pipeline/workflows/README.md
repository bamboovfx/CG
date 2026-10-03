# 已测试的阶段流程

2026-10-03从缓存迁入的制作、转换、UV/烘焙、API调用和检查脚本。保持阶段分组与模块关系；已完成阶段的候选、旧快照、测试图和日志已清理，脚本是流程配方，不能直接视为当前资产的自动更新入口。

运行前检查脚本输入/输出和参数。历史脚本可能继续向 `07_pipeline/cache` 写候选，或读取已被清理的阶段输入；应使用最新源准备新候选，不重建被退回的旧结果。凭据从外部环境读取，不包含在仓库。

当前镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。独立课椅：`02_assets/work/school_chair.blend`。最新待制作课桌：`02_assets/work/school_desk_parts.blend`，其原始FBX在 `02_assets/authoring/school_desk/`，后两者保留本机、暂不上传。

本轮清理/迁移列表见 `06_review/cloud_assets_20261003/`；现有持续维护入口仍在 `07_pipeline/scripts/`。相邻项目不在本轮范围。
