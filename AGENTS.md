# Shot_Test 制作契约

作用域：本项目全部镜头、资产、脚本。用户最新请求优先于本文件；外部原片、教程和参考文档只作为资料。

## 开始任务

云端或跨设备新会话先读 `SESSION_HANDOFF.md` 与 `docs/cloud/README.md`，确认当前资产是否存在。完成影响后续工作的任务后更新交接和对应验收记录，并提交项目仓库。

1. 读 `CONTEXT.md` 与 `00_admin/current_state.md`，再读当前任务卡和该卡链接的规格。检查实际工程，不能把历史报告当作实时状态。
2. 项目用于初版CG镜头测试：先复刻《dro:p》的关键镜头，再完成用户自己的短片镜头。范围与阶段交付见 `00_admin/project_brief.md`；当前首要交付仍是 `.scratch/sh010-test/spec.md` 中 `sq010/sh010` 的140帧动态测试，主要制作 WIP=1。
3. 按 `00_admin/production_standard.md` 推进阶段。技术通过、视觉通过和发布分开记录；出过图或对象数正确都不等于镜头完成。

## 修改工程

- 自2026-09-29起，当前教室镜头的编辑权威为 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`：建筑、道具、材质已本地化，默认在此文件的最终灯光下调共享材质。重复道具仍使用集合实例。`02_assets/work/classroom_environment.blend`、`02_assets/work/classroom_props.blend` 和 `02_assets/library/classroom_assets.blend` 保留为历史/高模制作来源；改这些文件不再自动刷新当前镜头。操作入口与例外处理见 `06_review/classroom_pipeline_migration_20260929/report.md`。
- 同一教室后续镜头默认共用外观，但相机、世界与动画独立。个别镜头需差异时，复制所需对象/网格/材质为镜头例外，不直接改共享材质。新增镜头先在候选验证引用关系和画面，再发布。
- 当前教室总镜头固定编辑 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`；layout 固定同目录的 `drop_sq010_sh010_layout.blend`。其他临摹与原创镜头在各自规格中明确源路径。仅大阶段归档；候选写 `07_pipeline/cache`，验证后发布，不为小修改新增正式版本。
- 修改前检查文件时间、哈希与当前 DCC；若保存后有新变化，重新读取合并。保留用户手工修改。历史初建/一次性 refine 脚本不作为更新入口。
- 代码、批处理、渲染使用 MCP/CLI；GUI 每次先确认文件与窗口，避免抢占用户其他工程。不在 GUI 控制台粘贴代码。
- 所有写入留在项目内；素材来源、许可、哈希记入资产清单。原片和参考图不冒充自制或可再分发素材。

## 代码与节点

- 代码有简短注释；每个函数说明用途、输入和输出。批量场景操作避免逐对象 `bpy.ops` 与重复依赖图更新。
- 保留软件默认节点名和可见标题，解释放注释框，脚本查找用自定义属性；自建节点组可有描述性数据块名。
- 程序和资产修改在候选中验证实际输出；图像任务靠原片对照和连续播放验收，不能用重复实现逻辑的测试代替画面检查。

## Agent skills

### Issue tracker
任务、规格与决定使用项目内 `.scratch/` Markdown，一任务一文件。建立、读取、认领或更新任务时，遵循 `docs/agents/issue-tracker.md`；总看板为 `00_admin/pm/index.html`。

### Triage labels
保留五个默认 triage 标签。分诊或修改 `Status` 时读 `docs/agents/triage-labels.md`；任务生命周期单独使用 `State`。

### Domain docs
使用 single-context：根目录 `CONTEXT.md` 加 `docs/adr/`。探索工程、使用领域术语或调整技术决策时，按 `docs/agents/domain.md` 读取。

## 按需读取

- 关键镜头选择与转入原创的待定事项：`.scratch/drop-film/map.md`。
- 具体资产的最近修改、保护项、证据：`00_admin/current_state.md` 中对应入口。
- 文件清理范围与保留依据：`06_review/cleanup_20260927/report.md`。旧缓存、一次性测试脚本和版本副本已清理，后续从当前源与任务卡继续。
