# 三组木材调整

完成日期：2026-09-17T00:06:16。源工程 `02_assets/work/classroom_props.blend` 和发布库 `02_assets/library/classroom_assets.blend` 已更新。

| 材质组 | 资产 | 调整 |
|---|---|---|
| 01 | 桌子、椅子、讲台、教师桌 | 独立 SD 细木纹清漆，暖黄棕色；保留磨损，椅板侧边为 2.3 mm 夹层 |
| 02 | 黑板木框和木质托槽 | 复制原椅子木材网络，保留原粉笔灰层；绿色书写面不变 |
| 03 | 前方书架、设备柜 | 独立 SD 棕色长纹；各木板按长轴映射，门框横竖纹随结构变化 |

## 验证

- 源工程修改 43 个第一组槽、33 个第三组槽、14 个黑板槽；发布库分别为 41、33、14。差别来自源/库中保留的参考模型。
- 总镜头实际使用 `AST_school_desk_HP`；已包含该集合，24 桌 + 24 椅 + 1 讲台 + 1 教师桌共 50 个实例均读取第一组。
- 黑板 1 个实例、书架和柜体 2 个实例已核对。所有 253 个道具实例仍引用发布库；10 个建筑实例仍直连建筑源。
- 比较网格顶点/拓扑、原 UV、局部变换、父子关系和其他材质槽的哈希，未改变。新增独立 WoodGrainMeters UV，不覆盖原 UV。
- 重新打开总镜头完成 1920×810 / Cycles 64 samples 检查，缺失贴图 0。没有保存或修改总镜头的灯光、相机、墙色、摆位。
- 每个材质族单独保存，后续调整不会同步改变其他组。两张 SD 图输出 4K BaseColor/Roughness/Normal/Height/Grain/ScratchMask；颜色为 sRGB，其余 Non-Color，法线 OpenGL，贴图周期 0.6 m。

## 入口

- [前后对照](index.html)
- [原片与 8 张实物参考](../../01_preproduction/references/wood_groups/index.html)
- [SD 文件说明](../../02_assets/materials/wood_groups/README.md)
- [机器检查记录](validation.json)

总镜头重新打开即可读到新资产库；若已打开，可在 Outliner 的 Blender File / Libraries 中 Reload `classroom_assets.blend`。

恢复副本保存在 `07_pipeline/cache/wood_groups/source_before.blend` 与 `library_before.blend`。它们为原文件字节副本，恢复时先复制回各自原路径，以保持相对贴图路径正确。
