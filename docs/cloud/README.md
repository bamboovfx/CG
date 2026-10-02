# Shot_Test 云端配置

用户于2026-10-02选择：公开 `bamboovfx/CG` 保存上下文与脚本，场景资产保留本机。仓库根目录对应本机 `D:/00_projects/10_CG/Shot_Test`，云端检出根通常为 `/workspace/CG`；保留原来的相对路径结构。

## 官方流程

Settings → Codex Cloud → Environments：从官方仓库选择器选择 `bamboovfx/CG`，环境命名 `Shot_Test`，准备并测试，保存后 Publish。已发布环境的更新使用 Edit → Save and publish；同账号在其他设备选择 Work in → Cloud → **Shot_Test**。

旧 CG 环境曾运行成功，但设置列表显示“未知代码仓库”，不作为后续接续入口。Shot_Test 通过官方选择器保留仓库关联；更新安装和启动字段时不要重写 repositories 或用仓库名猜关联 ID。GitHub 仓库仍为 CG，没有新建或替换资产仓库。

官方文档：https://learn.chatgpt.com/docs/environments/cloud-environments

安装入口 `bash scripts/setup-cloud.sh` 下载官方 Blender 5.1.2 Linux x64，核对 SHA256，执行 `python3 scripts/check_workspace.py --blender .local/tools/blender-5.1.2-linux-x64/blender`。环境需允许 `download.blender.org`，其余采用 Package managers；无需账号凭据或 VPN。

已配置的安装与启动步骤先设置可写缓存，避免云端默认 home 缓存目录的缩略图写入提示：

```bash
# 将后台 Blender 缓存和独立验收生成物留在忽略目录。
cd /workspace/CG
export XDG_CACHE_HOME=/workspace/CG/.local/cache
mkdir -p "$XDG_CACHE_HOME/thumbnails/large"
python3 scripts/check_workspace.py --blender .local/tools/blender-5.1.2-linux-x64/blender
```

安装脚本还会在已有下载包时重新核对 SHA256。启动说明要求先读交接与当前状态，完成影响后续工作的任务后更新并提交相关记录。正式环境与新建任务的实测证据见 [verification.md](verification.md)。

## 验收含义

- 恢复入口与全部同步的 Python 脚本解析通过。
- 独立默认场景在 Blender 5.1.2 后台保存、重开，以 Cycles CPU 输出64×64图像并验证像素有变化。生成物写入 `.local/cloud-smoke/`。
- 正式教室、课椅、原片及贴图未迁入，验收报告明确列出缺失资产；烟雾图不是教室画面或艺术效果验收。

从本机运行同一检查时，可通过 `--blender` 指定实际安装的 `blender.exe`。它使用 factory-startup 创建独立场景，不连接正在工作的 Blender，也不保存正式文件。

## 执行入口和本机依赖

`07_pipeline/config/project.json` 保留原始本机路径，防止改变原工程语义；云端工具使用当前脚本所在仓库作为根目录。云端覆盖说明见 `docs/cloud/runtime.json`。旧管线脚本可能依赖本机素材、Windows路径、Substance Designer/Painter或本机 MCP；运行前读脚本和输入输出，不能批量执行历史制作脚本。

当前仅同步文档与脚本。评审中图片/视频的链接保留作本机证据指针，云端无法据此完成视觉判断。重要云端代码和决定提交推送，资产修改和本机验证结果回写对应任务及 `SESSION_HANDOFF.md`。
