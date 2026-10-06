# 外置镜头贴图与网格，保留本地shading编辑

State: in-progress
Status: ready-for-agent
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-10-06

## Acceptance

- [x] 当前保存源保护，内嵌图片逐张哈希与外置文件一致。
- [x] 网格外部链接，网格／UV／法线／属性和共享引用保持。
- [x] 材质及节点组本地可编辑，全部对象有效材质、动画、相机与世界保持。
- [x] 候选独立重开、shading实际改值恢复、同帧图像对照通过。
- [x] 发布前重新核对源并原位发布，完成正式文件重开。
- [ ] 依赖清单、交接和仓库提交完整，Git LFS超限推送得到实际验证。

## Evidence

- [规格](../spec.md)
- [原推送诊断](../../../06_review/git_push_check_20261006/report.md)
- [本轮发布验收](../../../06_review/shot_external_links_20261006/report.md)

## Comments

2026-10-06认领：以用户当前磁盘源661e8ec继续；无Blender GUI进程，所有工作使用独立后台候选。保留主镜头未提交保存与历史文件删除。旧Texture整理卡仍未完成，本任务不代替历史材质清理。
