# 迁移当前教室镜头为可直接编辑的共用材质工程

State: done
Status: ready-for-agent
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-09-29

## Problem

旧镜头依赖跨文件 Link，黑板等材质不能在最终灯光下方便编辑；制作源与发布库的材质版本又不相同。

## Acceptance

- [x] 从用户最新已保存正式镜头生成候选和恢复副本，不覆盖新保存的工作。
- [x] 保留相机、天空Action、时间设置及未改变的集合实例与变换。
- [x] 黑板书写面直接可选；其余实例材质可由镜头内入口定位和编辑。
- [x] 重开正式工程，测试共用材质与镜头例外的数据隔离。
- [x] 同帧同设置画面对照通过，并记录未解决的源资产问题。
- [x] 更新工程规范、当前状态、操作说明与恢复路径。

## Evidence

- [迁移记录及画面](../../../06_review/classroom_pipeline_migration_20260929/report.md)
- [候选结构检查](../../../07_pipeline/cache/classroom_pipeline_migration_20260929/validation.json)
- [正式文件重开检查](../../../07_pipeline/cache/classroom_pipeline_migration_20260929/published_validation.json)
- [发布哈希](../../../07_pipeline/cache/classroom_pipeline_migration_20260929/published.json)

## Resolution

2026-09-29：已发布到固定镜头路径。正式文件SHA256 `25fef6ac014f853ef93994e3ec9d0faa59dc35d63d4ccdb717ce6e3297ac116f`。263个其余集合实例保留，黑板书写面直接可选，247个材质选择入口不参与渲染。第1076帧画面对照平均每通道差0.00351/255。旧五张Tommy `opdef:` 贴图缺失照旧存在；它属于后续资产修复，不将本任务误标为成片。

## Comments

- 2026-09-29：用户要求继续已确认的管线方向。正式文件变更前进行哈希门禁；发布后重开检查。
