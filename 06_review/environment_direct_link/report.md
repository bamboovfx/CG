# 建筑直接引用迁移验证

日期：2026-09-16

已保存并重新打开正式文件：
`D:/00_projects/10_CG/Shot_Test/03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`

保留原总镜头实例，仅将下列集合的引用从 `02_assets/library/classroom_assets.blend` 改为直接引用 `02_assets/work/classroom_environment.blend`：

- AST_classroom_shell
- AST_classroom_corridor
- AST_classroom_door
- AST_window_wall_left
- AST_window_wall_corridor
- AST_curtain_rail
- AST_gathered_curtain_00
- AST_gathered_curtain_01
- AST_gathered_curtain_02
- AST_gathered_curtain_03

10 个原实例均无父对象；实例名称、位置、旋转、缩放保持原值。新旧集合的 instance_offset 一致，内部 1,586 个对象的世界矩阵差值为 0，父子关系一致。实际迁移、保存重开、Reload 前后的 12,031 条求值对象记录逐项比较通过（矩阵记录保留小数点后 7 位）。未手动重新摆放。

接通总镜头时，用户此前新增的 environment Link 已不存在；未再删除任何对象。迁移后仅有 10 个 environment 建筑集合和 10 个原建筑实例，无额外直接挂入场景的建筑集合。253 个道具实例保留 classroom_assets.blend 引用，两份 library 均保留，使用相对路径。

黑墙验证：`Front plaster wall` 使用 environment 中的 `Surface / SH SD sage mineral wall`，Mix (Legacy) 的 Color2 为线性 RGBA `(0.0166519694, 0.0189669281, 0.0135502750, 1)`。直接调用该 library 的 Reload 后参数和布局检查通过。正式镜头全相机验证渲染见 `black_wall_verified.png`，使用 50% 分辨率和 16 samples；未保存这些临时渲染设置。活动相机 `cam_sh010_main`，保留用户当前帧 2。缺失外部图片数为 0。

备份目录：
`D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/environment_direct_link_20260916/`

- `shot_disk_before.blend`：操作前磁盘总镜头。
- `shot_live_before.blend`：正式迁移前总镜头当前状态，含未保存修改。
- `environment_live_before.blend`：资产窗口未保存状态副本；没有覆盖资产源。
- `compare.json`、`live_validation.json`、`final_validation.json`：结构与引用验证。

后续操作：在 environment 源中保存修改，再在总镜头 Reload 对应的 environment library。仅 Reload 总镜头无法读取源窗口中尚未保存的修改。迁移完成时总镜头已保存，资产源的未保存状态已另存备份，本次未覆盖资产源。

