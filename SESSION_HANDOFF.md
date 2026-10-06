# Shot_Test 交接记录

**2026-10-06课桌整体材质与迁移：** 当前入口 `02_assets/work/school_desk.blend`，贴图 `02_assets/textures/generated/kokuyo_desk`。桌洞／挂钩／固定片与旧管架协调，脚套深色橡胶及有效法线；21张依赖的相对路径与内嵌哈希、独立重开、原几何UV／木材保护通过。SHA256 `139da734695fabd36589982f0824b8b3473608189e8076a200c23f5bdef586e8`；技术pass、艺术review，正式镜头未改。只保留工程与依赖贴图，旧缓存清理见[记录](06_review/kokuyo_desk_20261006/report.md)。

更新：2026-10-03。用户将公开 `bamboovfx/CG` 的范围扩大为当前镜头、实际依赖和已验证制作流程；场景和贴图通过 Git LFS 上传，未使用资产保留本机并排除上传。

2026-10-04追加：用户授权完整 `01_preproduction/` 的新增、修改和删除上传，包含原片、参考图和 PureRef 板；二进制继续使用 LFS，`.pur` 已纳入规则。此次待推送范围仅为该目录及必要配置/交接文档；其他本地资产和评审文件继续排除。原先误纳大量文件的未推送提交保留在本地 `backup/preproduction-upload-20261003` 分支。当前仓库 LFS 连接与 TLS 超时为30秒、并发4；实际上传验收以远程 HEAD 和 LFS 对象检查为准。

上传验收（2026-10-04 00:02，Asia/Shanghai）：目录提交 `e6db1a9` 已成功推送，228个实际文件全部纳入，目录无未提交差异；219个 LFS 对象约301MB 上传完成。远程 main 与本地提交哈希一致，再次 LFS 推送核验退出0，无缺失对象。原目录中的删除也已同步；其他本地文件保留。

## 跨设备上下文补齐（2026-10-04）

已读取D-XIANYI-SHI上的7条CG聊天68个轮次及本机课桌接续15轮；来源、覆盖范围、历史决定和未恢复项见[上下文恢复记录](06_review/context_recovery_20261004/report.md)。接续时沿用参考→一致多视图→Tripo智能网格/分件/UV→工艺与表现层→同光验证的流程，六类资产从课桌开始；当前课桌返工仍需实际模型检查与视觉评审。PureRef沿用原生Note一级标题与单套拉片规范。

本机Blender 5.2.2后台只读打开正式镜头，实测保存帧1071、1001–1100/24fps、cam_sh010_main、World=Sun、25个共享课椅实例，无外部blend库引用，源哈希未变。140帧目标、5张人物贴图和Arial Narrow缺失仍未解决。原交接所称保留的school_desk_parts.blend和approved_material_library.blend在本机缺失，不能认为已跨设备迁移。开始时主镜头与PureRef已有未提交修改，本轮保留。

早期椅子父聊天未能读取；部分更早分页未展开。总PM生成器因本机40条历史验收证据缺失而中止刷新，原任务验收状态未改。用户最新跨设备选择是先用Connections访问原聊天；SSH没有在本轮安装或配置。

## 接续顺序

读 `AGENTS.md`、`CONTEXT.md`、`00_admin/current_state.md`，再读当前任务卡及其规格。新云端任务同时读 `docs/cloud/README.md`，先确认资产是否实际存在。历史文档引用的图片和工程不一定包含在公开仓库中。

## 当前制作状态

- 项目先复刻 Drop 关键镜头，再制作个人短片；当前首要目标为 `.scratch/sh010-test/spec.md` 的 sq010/sh010、24fps、1001–1140 共140帧动态测试。技术、视觉和发布分开记录。
- 本机编辑权威：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。2026-10-01 最新共享课椅实例修订记录在 `00_admin/current_state.md`；旧建筑/道具库不是当前镜头的自动刷新入口。
- 记录显示25把课椅共享母资产，保留主相机、1076帧、1001–1100/24fps、原世界与动作；这尚未达到140帧最终目标。视觉状态以任务卡和用户审阅为准。
- 整椅工艺/表现工作流已获用户确认；场景替换与最新共享实例方案的视觉仍待审阅。5张历史 Houdini opdef 图像未解析的问题仍需实际工程复核。

## 云端范围

同步制作约定、任务、文档、Python 管线脚本，以及当前镜头、外部贴图依赖、独立课椅和对应原生 SBS 配方/图片输入。本机为 Blender 5.1.2，云端使用同版 Linux 后台。资产上传范围由 `.gitignore` 白名单和 `06_review/cloud_assets_20261003/upload_manifest.json` 控制；10月4日追加完整 `01_preproduction/`，不受此前资产清单限制。渲染、缓存、SBSAR和未引用资产继续保留本机。Shot_Test 云端环境共享保持 Only me。

云端检出后先 `git lfs pull`，再运行 `python3 scripts/check_cloud_assets.py --hash`；只有 LFS 指针时不能打开工程。镜头仍有此前已缺失的5张 opdef 测试人物贴图，并依赖未上传的 Arial Narrow 系统字体。云端实际重开/渲染和用户视觉验收应另行记录，不能由上传或默认烟雾验收推断通过。资产修改前继续核对文件时间、哈希与用户手工修改。

本轮删除524个缓存、旧候选和备份文件（56,395,303,895字节），迁移72项最新源与制作流程并核对SHA256。课椅入口移至 `02_assets/work/school_chair.blend`；最新课桌和材质库移到 `02_assets/work/`，尚未用于镜头，暂不上传。140帧候选工程在本轮开始前已缺失，预览视频与流程记录仍在。详见 `06_review/cloud_assets_20261003/report.md`。

## 配置结果

公开仓库已推送，官方 **Shot_Test** 环境已保存并发布，权限为 Only me。电脑 Chrome 从新聊天选择 Shot_Test 后创建的[独立云端验收任务](https://chatgpt.com/local/01a0fb72-6829-75d5-b039-25e0c667103f)通过；实际检出 `/workspace/CG`，准备基线 `99ab2ea3a10c1858c71366af8aa4b9a948697c5f`，Python 3.12.14、Blender 5.1.2。

159个受控 Python 脚本解析、独立场景保存/重开、64×64 Cycles CPU 渲染与像素变化检查退出0，前后 Git 状态干净。正式资产缺失、未验收。缓存使用 `.local/cache`，生成物均忽略。完整证据见 `docs/cloud/verification.md`；制作进度保持原验收状态。

后续入口统一为 **Shot_Test**，GitHub 仓库仍为 `bamboovfx/CG`。旧 CG 虽运行通过，但仓库关联显示异常，保留作历史配置。Shot_Test 从官方仓库选择器重建，设置列表正确显示 `bamboovfx/CG`。更新脚本配置时保留官方仓库关联。

其他设备登录同账号后选择 Work in → Cloud → **Shot_Test**。当前任务的源码与上下文恢复以实际 HEAD、已提交文件为准；后续更新通过仓库刷新进入云端，不把准备快照的旧交接状态当作最新制作状态。
