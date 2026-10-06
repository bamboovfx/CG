# 整理当前镜头贴图与清理历史材质

State: blocked
Status: ready-for-agent
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-10-06

## What to build

按用户2026-10-06授权，核查固定shot及独立课椅实际依赖，统一整理到02_assets/Texture；清理没有采用或复现价值的历史材质。先确认凳子是否使用SD。此项是依赖维护，不改变镜头制作与视觉验收状态。

## Acceptance criteria

- [x] 实际重开最终shot，列出使用材质与贴图，确认SD来源。
- [ ] 当前使用贴图统一存放，哈希和来源可追溯。
- [ ] 清理未使用历史材质，保留有复现价值的配方及输入。
- [ ] 候选重开、同帧渲染比较、源发布前保护检查通过。
- [ ] 更新交接、资产清单并提交本任务修改。

## Evidence

- [依赖审计，zlib/base64 JSON](../../../06_review/texture_cleanup_20261006/shot_audit.zlib.b64)
- [本轮报告](../../../06_review/texture_cleanup_20261006/report.md)

## Next

先停止仓库自动diff/LFS反复处理。空间曾为0，后续其他操作清理后短暂达到约264GB，但再次快速消耗；已捕获Codex桌面Git diff -> Git LFS filter-process进程链。详见本轮报告。随后完成独立课椅审计、候选迁移和验证。

## Comments

2026-10-06：用户此前已有主镜头、独立课椅、PureRef修改和大量评审文件删除。本任务保留现存状态，不恢复或提交无关改动。

2026-10-06：最终shot只读重开，309个已绑定材质、465个图像数据块；除Render Result/Viewer Node外均存在材质节点引用，不能据此认定所有节点对输出有效。打包数据约1.811GB。SD来源确认；尚未实施Texture迁移或完成最终材质清理。两张Process_Height曾因只查shot引用而误判为未用输出，发现SD配方输入引用后已用同SHA256本地LFS对象恢复；architecture_linen.sbs也已恢复原SHA256。本轮不提交未完成整理。
