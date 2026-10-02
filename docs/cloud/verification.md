# Shot_Test 云端配置验收

2026-10-02；公开仓库 `bamboovfx/CG`，main。配置准备基线 `04bd62ec85a749f4e0a8cbb637ea83e6f5ed8256`。公开内容仅为上下文、任务、配置与脚本；正式资产保留本机。

## 本机

Python 3.12.10、官方 Blender 5.1.2 Windows。执行 `python scripts/check_workspace.py --blender "D:/Program Files/Blender Foundation/Blender 5.1/blender.exe"` 退出0：159个受控 Python 脚本解析、独立默认场景保存/重开、Cycles CPU 64×64渲染与像素变化检查通过。结果文件记录 `formal_scene_tested: false`。本机正式镜头和课椅存在，但此次未打开或验证它们。

## 云端设置实例

[编辑 CG](https://chatgpt.com/local/01a0fb5f-0bcb-7341-b757-069dce1cf0f5)，检出 `/workspace/CG`，HEAD为上述基线。旧空仓库需获取main：fetch退出0，首次通过origin/main切换退出128（该远端引用不存在）；保留工作区并从FETCH_HEAD创建main退出0，随后核对HEAD与文件。

从 `download.blender.org` 下载官方 Blender 5.1.2 Linux x64；SHA256为 `aaccb355f50183979b698bcce7467103a76261b5fa59f4972295842662a285fb`，校验通过，构建 `ec6e62d40fa9`。工具：Python 3.12.14、Git 2.52.0、curl 8.14.1、coreutils 9.7、tar 1.35。系统库已齐全，未安装额外系统依赖。

首轮 `bash scripts/setup-cloud.sh` 退出0。默认home的缩略图缓存目录出现不可写提示，改为 `XDG_CACHE_HOME=/workspace/CG/.local/cache` 并创建 `thumbnails/large` 后复测退出0且无此提示。完整安装脚本与启动验收命令分别实测退出0；159个脚本解析、独立场景保存/重开、CPU渲染与像素检查全部通过。生成物仅写入忽略的 `.local/`，最终Git状态干净、差异检查退出0。

安装脚本和启动说明已保存。网络为Package managers加 `download.blender.org`，无额外凭据或环境变量；页面已核对使用权限为Only me。

## 验收边界

云端缺少正式镜头、独立课椅及本机素材；独立默认场景通过不代表正式工程依赖、画面或艺术效果通过。未上传资产、重建教室或运行历史制作/清理脚本。此配置不改变制作任务的验收状态。

## 发布及全新任务

官方页面实际显示“已发布”。电脑 Chrome 从新聊天搜索并选择 CG，创建[全新验收任务](https://chatgpt.com/local/01a0fb67-bd0e-7274-a225-c72b5c80f015)，没有续接设置任务或手机聊天。

本次实际环境已连接，origin为 `https://github.com/bamboovfx/CG.git`，初始pwd为 `/workspace`，检出目录 `/workspace/CG`，HEAD为上述准备基线。设置可写缓存后执行 `python3 scripts/check_workspace.py --blender .local/tools/blender-5.1.2-linux-x64/blender` 退出0：159个脚本解析通过、独立场景保存与重开通过、Cycles CPU 4 samples / 64×64渲染及像素检查通过。正式镜头和独立课椅缺失；结果JSON为 `formal_scene_tested: false`。初始与最终Git状态均为空，忽略规则确认生成物未进入仓库。

新任务使用准备快照04bd62e；本文件及更新的交接记录是验收后补录的提交。以后接续核对实际HEAD和仓库刷新结果；历史设置记录不替代实时状态。
