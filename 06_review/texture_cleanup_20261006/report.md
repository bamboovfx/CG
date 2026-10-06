# 当前shot贴图整理调查

日期：2026-10-06。状态：只读调查完成；迁移与清理未完成，未发布。

Blender 5.2.2后台重开固定shot：309个材质均有对象材质槽绑定；465个图像数据块，除Render Result/Viewer Node外均被材质节点引用。节点引用不等同于对shader输出有效，后续仍需追踪有效输出。已有5张Houdini opdef人物贴图和Arial Narrow字体缺失。镜头保存帧1071、1001–1100、24fps、cam_sh010_main；未保存主工程。

凳子确实使用SD。原生配方：tripo_wood_reference（木材工艺）、tripo_wood_detail（磨损/老化）、tripo_wood_dirt（脏渍）、chair_metal_layers（金属）、chair_foot_caps（胶脚）。最终shot引用对应Process_*、Raw_*、Dirt*、Paint*等输出。保留这些配方及完整图片输入，不能将它们视为失败历史稿全部删除。

原始审计以shot_audit.zlib.b64保留，可用Python的base64.b64decode和zlib.decompress还原JSON。初步迁移目标为02_assets/Texture，保留当前输出和有复现价值的SD配方/输入，统一相对路径；删除名单须经过有效shader和独立课椅依赖核查。

F盘最初可用空间0。仓库.git/lfs/tmp有997个临时文件，合计305122956288字节；起初无git-lfs进程的检查只代表瞬时状态。对最旧20个临时文件的删除被自动审批以blocked by policy拦截，操作未执行，已向用户询问明确授权。未绕过拦截。

后续用户询问占满原因，实测纠正了“下载临时文件”的称呼：8个大文件样本的前1MiB SHA256分别匹配school_chair.blend或固定shot，均为本地工程处理的临时副本。直接捕获进程链：Codex安装目录下ChatGPT.exe PID38180 -> git diff（含两份blend）-> sh.exe -> git-lfs filter-process，两个独立diff进程链均指向同一Codex进程。UGit亦观察到push与LFS活动，但尚不能将历史全部临时文件归给UGit。Git LFS官方clean实现先将输入复制到临时文件，未成功返回cleanedAsset时不会走正常Teardown删除。

本轮只读诊断期间有其他操作清理临时文件：从1008个约305.123GB降到47个约40.415GB，可用空间达到264067780608字节，下一次读取已降至255137378304字节，仍存在快速写入。此清理由其他操作完成，本任务没有执行此前被拦截的删除。应先停止仓库自动diff/LFS反复处理，再进行剩余清理与Texture迁移。

调查时两张Process_Height曾误判为未用输出，发现SD引用后已按原SHA256恢复，architecture_linen.sbs亦恢复；恢复图片暂与本地LFS对象硬链接，后续迁移需复制为独立文件。无正式blend写入，无Texture迁移，无完成提交。后续先解决空间，再完成候选重开和同帧渲染比较、发布保护、资产清单与交接更新。
