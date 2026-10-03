# Shot_Test 交接记录

更新：2026-10-03。用户将公开 `bamboovfx/CG` 的范围扩大为当前镜头、实际依赖和已验证制作流程；场景和贴图通过 Git LFS 上传，未使用资产保留本机并排除上传。

## 接续顺序

读 `AGENTS.md`、`CONTEXT.md`、`00_admin/current_state.md`，再读当前任务卡及其规格。新云端任务同时读 `docs/cloud/README.md`，先确认资产是否实际存在。历史文档引用的图片和工程不一定包含在公开仓库中。

## 当前制作状态

- 项目先复刻 Drop 关键镜头，再制作个人短片；当前首要目标为 `.scratch/sh010-test/spec.md` 的 sq010/sh010、24fps、1001–1140 共140帧动态测试。技术、视觉和发布分开记录。
- 本机编辑权威：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。2026-10-01 最新共享课椅实例修订记录在 `00_admin/current_state.md`；旧建筑/道具库不是当前镜头的自动刷新入口。
- 记录显示25把课椅共享母资产，保留主相机、1076帧、1001–1100/24fps、原世界与动作；这尚未达到140帧最终目标。视觉状态以任务卡和用户审阅为准。
- 整椅工艺/表现工作流已获用户确认；场景替换与最新共享实例方案的视觉仍待审阅。5张历史 Houdini opdef 图像未解析的问题仍需实际工程复核。

## 云端范围

同步制作约定、任务、文档、Python 管线脚本，以及当前镜头、外部贴图依赖、独立课椅和对应原生 SBS 配方/图片输入。本机为 Blender 5.1.2，云端使用同版 Linux 后台。上传范围由 `.gitignore` 白名单和 `06_review/cloud_assets_20261003/upload_manifest.json` 控制；原片、参考网站照片、渲染、缓存、SBSAR和未引用资产保留本机。Shot_Test 云端环境共享保持 Only me。

云端检出后先 `git lfs pull`，再运行 `python3 scripts/check_cloud_assets.py --hash`；只有 LFS 指针时不能打开工程。镜头仍有此前已缺失的5张 opdef 测试人物贴图，并依赖未上传的 Arial Narrow 系统字体。云端实际重开/渲染和用户视觉验收应另行记录，不能由上传或默认烟雾验收推断通过。资产修改前继续核对文件时间、哈希与用户手工修改。

本轮删除524个缓存、旧候选和备份文件（56,395,303,895字节），迁移72项最新源与制作流程并核对SHA256。课椅入口移至 `02_assets/work/school_chair.blend`；最新课桌和材质库移到 `02_assets/work/`，尚未用于镜头，暂不上传。140帧候选工程在本轮开始前已缺失，预览视频与流程记录仍在。详见 `06_review/cloud_assets_20261003/report.md`。

## 配置结果

公开仓库已推送，官方 **Shot_Test** 环境已保存并发布，权限为 Only me。电脑 Chrome 从新聊天选择 Shot_Test 后创建的[独立云端验收任务](https://chatgpt.com/local/01a0fb72-6829-75d5-b039-25e0c667103f)通过；实际检出 `/workspace/CG`，准备基线 `99ab2ea3a10c1858c71366af8aa4b9a948697c5f`，Python 3.12.14、Blender 5.1.2。

159个受控 Python 脚本解析、独立场景保存/重开、64×64 Cycles CPU 渲染与像素变化检查退出0，前后 Git 状态干净。正式资产缺失、未验收。缓存使用 `.local/cache`，生成物均忽略。完整证据见 `docs/cloud/verification.md`；制作进度保持原验收状态。

后续入口统一为 **Shot_Test**，GitHub 仓库仍为 `bamboovfx/CG`。旧 CG 虽运行通过，但仓库关联显示异常，保留作历史配置。Shot_Test 从官方仓库选择器重建，设置列表正确显示 `bamboovfx/CG`。更新脚本配置时保留官方仓库关联。

其他设备登录同账号后选择 Work in → Cloud → **Shot_Test**。当前任务的源码与上下文恢复以实际 HEAD、已提交文件为准；后续更新通过仓库刷新进入云端，不把准备快照的旧交接状态当作最新制作状态。
