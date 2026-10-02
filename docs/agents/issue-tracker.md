# Issue tracker: Local Markdown

项目任务与规格存放在 `Shot_Test/.scratch/`，以下路径均相对 `Shot_Test` 根目录。它是持久 PM 数据，虽沿用 skill 的目录名，不作为临时缓存清理。沿用2026-09-20确认的本地方案；2026-09-27重新配置时保留已有卡片与状态。

## 权威位置

- 规格：`.scratch/<effort>/spec.md`。
- 任务：`.scratch/<effort>/issues/NN-title.md`，一任务一文件，前置任务优先编号。
- 决定地图：`.scratch/drop-film/map.md`；只索引决定，详细答案放决定卡中。
- `sh010-test` 保留当前教室测试；`drop-film` 保留参考选择与阶段决定。后续临摹任务用 `drop-<shot>`，原创任务用 `original-<shot>`，开始对应镜头时再建目录与规格。
- 卡片中的 `State`、`Owner`、`Blocked by`、验收和证据是权威。HTML 看板是生成物，不直接改状态。
- `00_admin/shot_status.json` 保留旧历史，不能作为当前任务状态来源。

## Skill 读写约定

- “发布到 issue tracker”：在相应 effort 的 `issues/` 新建独立任务卡；已有同一任务时原位更新。
- “读取 ticket”：读取用户给出的文件路径；仅有编号时，先在当前 effort 的 `issues/` 中解析。
- 在卡片 `## Comments` 末尾追加带日期的讨论与决定；保留此前验收证据。
- 更新任务后运行 `python 07_pipeline/scripts/build_production_pm.py`，校验依赖并刷新看板。

## 状态与工作选择

`State`：`backlog` 未就绪；`ready` 可开始；`in-progress` 已认领；`review` 待视觉评审；`blocked` 有明确阻塞；`done` 已通过；`cancelled` 明确取消。

`Status` 使用 triage 标签。任务有 `ready-for-agent` 标签仍可能被前置阻塞；标签与完成状态不是一回事。

1. 读取任务及全部未完成前置；只有前置为 `done` 的任务可进入 `in-progress`。取消前置不自动解锁，先重新审查依赖。
2. 认领时先写 `Owner` 和 `State: in-progress`，再工作。同一制作镜头主要任务 WIP=1；独立只读调查可并行。
3. 每轮更新已完成验收、实际证据、未通过项和唯一下一步；状态变化附日期。任何阻塞写原因与解锁动作。
4. 技术已通过而视觉未通过时写 `review`；代理不能代用户确认艺术效果。
5. `done` 必须勾选全部验收并有存在的证据。重开修改保留先前结论，以新评论记录原因。

## Wayfinding operations

决定卡是地图的子文件，`Type` 为 research/prototype/grilling/task，用 `Blocked by` 文件链接表示依赖。开放、无前置阻塞、无人认领的卡构成当前可处理队列。结论追加到 `## Resolution`，完成后才把具名链接加入地图 Decisions so far。关键镜头和原创阶段尚不能准确表述的问题留在 Not yet specified，明确范围后再拆任务。

Skill 通用步骤中的 claimed/resolved 分别映射为本项目 `State: in-progress/done`；`Status` 始终保留五个 triage 标签之一，避免覆写标签。当前选定镜头之外的全片参考是资料，不自动生成制作任务。

读写和发布都在本地完成；不创建外部账号、Issues、消息或定时任务。
