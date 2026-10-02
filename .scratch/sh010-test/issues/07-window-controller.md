# 为当前选中的外窗活动窗扇建立控制器

State: done
Status: ready-for-agent
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-09-27

## What to build

按用户本轮明确请求，给建筑源中当前选中的 `WIN clear 5mm glass.006` 所属下部活动窗扇建立一个 Empty 父级，方便沿轨道统一平移。此项为单独的资产操作辅助，不代表动态 Blocking 已通过。不继续先前已取消的代做风场与窗帘动画。

## Acceptance criteria

- [x] 活动窗扇的玻璃、框、密封条、压条、拉手与配对锁扣绑定同一个控制器。
- [x] 绑定前后世界变换保持；试滑时只有目标窗扇部件移动。
- [x] 相邻窗、固定外框、轨道、上亮窗及用户当前材质修改保持。
- [x] 当前建筑源保存并验证，控制器选中，使用方法明确。

## Evidence

- [制作与操作记录](../../../06_review/window_controller/report.md)
- [正式绑定与试滑验证](../../../06_review/window_controller/published_validation.json)
- [正式源重开验证](../../../06_review/window_controller/reopened_validation.json)

## Next

用户在建筑源选中 `ctrl_window_left_04` 后用 `G Y` 推拉；Location Y=0 恢复原位置。本轮控制器任务已完成，不继续代做此前取消的风动。

## Comments

2026-09-27：当前对象由实时建筑源确认，用户此前已自行保存新材质修改。采用其最新文件制作候选，不恢复9月19日旧源。

2026-09-27：候选通过后，在实时窗口的新未保存内容上应用绑定并保存，恢复副本包含这些用户改动。20部件跟随检查通过，固定部分不动，保存重开通过。
