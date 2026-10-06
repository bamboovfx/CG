# Shot_Test 云端配置

2026-10-06当前恢复入口：主镜头引用 `02_assets/library/classroom_geometry.blend` 与项目内外置贴图，材质和节点组仍在镜头内编辑。当前依赖清单为 `06_review/shot_external_links_20261006/upload_manifest.json`，`scripts/check_cloud_assets.py --hash` 优先核对该清单。恢复时带齐LFS库和贴图；[外部链接验收](../../06_review/shot_external_links_20261006/report.md)说明当前编辑入口与既有资源缺口。下方10月3日准备清单和软件参数保留为历史。

2026-10-03：用户将同步范围扩大为当前镜头、实际资源依赖和已验证的制作流程。仓库仍为公开 `bamboovfx/CG`，根目录对应本机 `D:/00_projects/10_CG/Shot_Test`；云端通常检出 `/workspace/CG`，保持相对目录结构。

2026-10-04追加：用户要求上传完整 `01_preproduction/` 的改动，包含原片、参考图、PureRef 板及目录中的删除。该目录已完整放开白名单，秘密、日志和临时文件仍排除；`.pur` 与图片、视频一起使用 LFS。其他资产和评审目录不因这次上传而扩大范围。

## 恢复资产

场景、贴图等二进制使用 Git LFS；uGit 和命令行共用 `.gitattributes`。`.gitignore` 默认排除素材，只有依赖审计后的文件进入白名单。新增镜头或资产后应更新审计与白名单。

```bash
# 下载当前版本的真实二进制，再核对尺寸和完整性。
git lfs install --local
git lfs pull
python3 scripts/check_cloud_assets.py --hash
```

上传清单与哈希：`06_review/cloud_assets_20261003/upload_manifest.json`；清理、迁移和重开证据见同目录。权威场景为 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`，独立课椅入口为 `02_assets/work/school_chair.blend`。最新课桌、旧建筑/道具源、未引用贴图不在本轮上传范围，仍保留本机。

当前资产族的原生 SBS 图和显式图片输入保留为可编辑流程；SD/SP 仍是本机工具，SBS 的原始 Windows 来源路径继续保留，跨设备编辑前须重映射。编译 SBSAR、渲染序列、测试快照、日志、缓存和运行时不上传。原片与参考网站照片按10月4日追加授权随 `01_preproduction/` 上传。历史评审图链接是本机证据指针，不保证云端有图像。

## 官方环境与安装

继续使用从官方仓库选择器关联 `bamboovfx/CG` 的 **Shot_Test** 环境，共享为 Only me。旧 CG 环境关联曾显示异常，不作为接续入口。已发布环境更新使用 Edit → Save and publish；保留官方仓库关联，不猜测或重写关联 ID。

安装入口 `bash scripts/setup-cloud.sh` 先准备 Git LFS 并拉取资产，再下载官方 Blender 5.1.2 Linux x64，核对 SHA256，运行 `scripts/check_workspace.py`。环境除 `download.blender.org` 和 Package managers 外，还需允许实际 GitHub LFS 下载端点；网络阻断时根据失败 URL调整，不将只有指针的检出认作资产恢复。

```bash
# 将后台缓存与独立验收生成物留在忽略目录。
cd /workspace/CG
export XDG_CACHE_HOME=/workspace/CG/.local/cache
mkdir -p "$XDG_CACHE_HOME/thumbnails/large"
python3 scripts/check_workspace.py --blender .local/tools/blender-5.1.2-linux-x64/blender
```

其他设备登录同账号后选择 Work in → Cloud → Shot_Test。云端新任务先读 `SESSION_HANDOFF.md` 与 `00_admin/current_state.md`，检查 HEAD 和实际 LFS 资产，不能采用10月2日“仅有脚本”的旧快照结论。

## 验证与既有限制

本轮本机执行了保留工程后台重开、迁移哈希保护与上传文件检查。正式镜头仅规范项目内外部路径和磁盘压缩；保存重开前后核对几何/UV/法线、材质节点与打包图像、集合实例、动作、相机/帧范围和场景设置。实际结论以本轮证据为准，默认烟雾场景不能代替教室画面验收。

镜头在本轮开始前已有5张 Houdini opdef 测试人物贴图未解析，仍依赖 `C:/Windows/Fonts/ARIALN.TTF`。系统字体未复制到公开仓库；Linux恢复需自行提供可用字体，或另行批准替代方案。镜头仍为1001–1100/24fps，140帧目标未完成。文档中的 `pose_fit_candidate.blend` 在本轮清理前已缺失；其预览视频和制作记录留在本机。

仓库上传不代表已在发布云端环境完成正式镜头渲染或视觉验收。旧云端准备与烟雾验收见 `verification.md`，其历史日期和基线继续保留。
