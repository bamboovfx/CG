# 教室模块资产与 SD 材质交付

本轮重做并替换39个剩余模块，保留已完成的桌椅；固定镜头和资产库继续使用原路径。

| 分组 | Blender 源 | 原生 SD 图 | 评审 |
|---|---|---|---|
| 建筑 / 窗帘 | [classroom_architecture.blend](D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_architecture.blend) | [architecture_rebuild](D:/00_projects/10_CG/Shot_Test/02_assets/materials/architecture_rebuild) | [参考与近景](D:/00_projects/10_CG/Shot_Test/06_review/architecture_rebuild/review_sd.md) |
| 木柜 / 设备 | [classroom_equipment.blend](D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_equipment.blend) | [equipment_rebuild](D:/00_projects/10_CG/Shot_Test/02_assets/materials/equipment_rebuild) | [参考与近景](D:/00_projects/10_CG/Shot_Test/06_review/equipment_rebuild/review.md) |
| 黑板 / 教学陈设 | [classroom_teaching.blend](D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_teaching.blend) | [teaching_rebuild](D:/00_projects/10_CG/Shot_Test/02_assets/materials/teaching_rebuild) | [参考与近景](D:/00_projects/10_CG/Shot_Test/06_review/teaching_rebuild/review.md) |
| 房间壳体 / 糖果罐 | [classroom_shell_tin.blend](D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_shell_tin.blend) | [shell_tin_rebuild](D:/00_projects/10_CG/Shot_Test/02_assets/materials/shell_tin_rebuild) | [参考与近景](D:/00_projects/10_CG/Shot_Test/06_review/shell_tin_rebuild/review.md) |

共 25 个可编辑 `.sbs` 和对应实编译 `.sbsar`。每组保留真实 SAT 调用、输入/输出哈希、seed、尺寸和通道语义。Blender 使用2K/4K导出图；材质族共享，避免每个物件复制一套。

扫描输入为项目既有 Poly Haven / ambientCG CC0 素材；实物近景照片仅作为参考。柜体加入真实板厚、门框、嵌板、3mm门缝与局部清漆磨损，木纹随板件方向。木质书架、黑板框和讲台统一同类清漆表面；地板改成303mm方格五条拼木、旧漆光泽变化与细缝。

窗帘重新做侧向束拢、挂点短褶、局部斜向张力褶和自由边卷转。每片为连续布面，Cloth置于Subdivision/Solidify之前；顶部pin和束带提示组已保留。**微风动力学尚未启用或烘焙。** 开始模拟时须设置束带约束/碰撞，或先移除束带改自由帘。

整景检查修正了新玻璃朝内法线造成的错误反射，并恢复仅阴影射线使用的薄窗透射近似。已渲染检查全景、木柜、窗帘、教学区域，保留原相机与灯光。24套桌子开口朝各自椅子；167个罐体姿态不变；15本书按新层板做接触高度修正。

本轮读回验证：41个在用集合、261个实例、207张实际依赖图，无丢图；150张依赖来自SD生成目录。完整数据见 [validation.json](validation.json)。

参考范围为原片02:32–02:52。已查看152/154/160/166/168/170/172秒等帧，外形与材质细节另参考制造商和实物照片。房间尺度、不可见背面结构和印刷内容中有制作设定，本轮是模块资产与材质升级，不标记为原片镜头最终匹配。

渲染：
![整景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/modular/v001/scene.png)
![木柜与书架](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/modular/v001/cabinet.png)
![窗帘](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/modular/v001/curtain.png)