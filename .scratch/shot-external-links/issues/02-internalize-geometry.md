# 将模型恢复到镜头内部

Type: task
State: done
Status: ready-for-agent
Owner: Codex
Blocked by: none
Updated: 2026-10-07
Spec: [.scratch/shot-external-links/spec.md](../spec.md)

## Acceptance

- [x] 当前模型、UV及属性全部保留，网格在镜头内可编辑，无外部blend依赖。
- [x] 原材质、节点、实例、相机与动画保留；贴图继续使用外部相对路径。
- [x] 候选与发布版本独立重开、实际几何／shading修改恢复及同帧预览通过。
- [x] 更新依赖清单、制作契约与交接，提交并同步Git。

## Evidence

- [恢复验收](../../../06_review/shot_internal_geometry_20261007/report.md)
- [正式重开](../../../06_review/shot_internal_geometry_20261007/published_verification.json)

- [推送验收](../../../06_review/shot_internal_geometry_20261007/push_receipt.json)

## Comments

2026-10-07：用户明确“模型不要放到外部，就放到内部就行”。重开外部几何决定；贴图外置与本地shading保留，历史库不再作为当前模型编辑入口。

2026-10-07发布：11,033个本地网格、313个原材质、46个节点组保持；正式源450e8122／63.24MiB，外部blend依赖0。保护快照无变化，84张外置载荷哈希、全图像解释与路径、实际几何及shading改值恢复、候选／正式重开和同帧预览通过。Git同步待验证。

2026-10-07完成：f57962c已快进推送，1个66MB LFS对象上传完成，远程HEAD与本地一致；首次连接重置后正常重试成功。本任务技术通过并发布，镜头艺术验收不变。
