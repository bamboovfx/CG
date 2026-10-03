# 工具入口

2026-09-27清理后保留维护、参考提取与材质生成代码；旧阶段的一次性探测、提交、对比渲染及修改脚本已清理。逐文件记录见 `../../06_review/cleanup_20260927/manifest.json`。

- `build_production_pm.py`：从当前任务卡刷新PM看板，不修改任务状态。
- `audit_cleanup_dependencies.py`：后台只读重开固定工程和当前候选，检查外部资源；不保存blend。
- `production_audit.py`：原有镜头审计入口；运行前核对其报告输出路径。
- `render_sh010.py`：对已打开的镜头做单帧预览或beauty；不是140帧动画发布工具。
- `collect_*`、`extract_film_reference_frames.py`、`reference_upgrade_research.py`：参考收集与拉片工具。
- 材质生成、SBS编译和贴图导出脚本：保留其本地模块依赖。现有 `.sbs` / `.sbsar` 与工作blend是编辑源；旧生成器反映初建步骤，运行前核对输入和输出，不能直接覆盖之后的手工修改。
- `build_sh010.py` 与 `cloth_tone_simulate.py`：保留初建/模拟配方供理解与受控重算；当前镜头和布料源已分别保存，不需要为日常继续制作重跑。

当前140帧候选的制作/渲染配方在 `../../06_review/production_audit_20260920/character/`。2026-10-03实查，旧候选工程和先前记录的FFmpeg缓存运行时已不在磁盘；视频与配方仍保留，需重新准备运行时后再运行历史渲染流程。

2026-10-03缓存清理时，将可复现的阶段脚本迁到 `../workflows/`，最新课椅源迁到 `../../02_assets/work/school_chair.blend`。新的只读重开入口是 `../../scripts/audit_cloud_assets.py`，上传完整性入口是 `../../scripts/check_cloud_assets.py`；旧日期审计脚本仅用于理解当时验收，不覆盖本轮证据。

新增临时产物统一放 `../cache/<task>/`。评审视频验证后只保留当前候选、必要样帧和证据；新候选取代旧候选时更新任务卡，再清理失效版本。
