# 核实镜头参考与当前工程

State: done
Status: ready-for-agent
Owner: Codex
Type: research
Blocked by: None
Updated: 2026-09-20

## What to build

让用户可以对照实际源帧、最新工程渲染和动作证据，知道140帧测试的起点及差距。

## Acceptance criteria

- [x] 实测本地参考时基、时长和音轨状态。
- [x] 相邻帧确认主全景边界，区分下一镜落座。
- [x] 重开最新总镜头，检查依赖、动画与输出设置，给出主机位图。
- [x] 比较人物与同排椅子，纠正相机运动与人物运动的混淆。

## Evidence

- [原片审计](../../../06_review/production_audit_20260920/film_audit.md)
- [当前场景](../../../06_review/production_audit_20260920/scene_audit.json)
- [动作修正与测量](../../../06_review/production_audit_20260920/hero_motion_guide.md)

## Next

按相机揭示人物制作全长Blocking。

## Capability evidence

代理完成媒体、工程和投影资料核对。初次低频采样误判走入，后以高分辨率相对运动纠正；制作指令以最新guide为准。这个任务通过的是证据完整性，不是镜头视觉质量。
