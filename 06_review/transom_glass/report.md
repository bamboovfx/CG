# 上亮窗改为玻璃 · 2026-09-19

用户红圈内的三段上亮窗共 12 块面板，以及门上方 1 块面板，改用下方窗户现有的 `ARC SD clear window glass` 材质。厚度统一为 5 mm，玻璃边缘倒角为 0.2 mm。保留原窗框、分隔、安装位置与窗洞覆盖面积。

修改入口：`02_assets/work/classroom_environment.blend`。总镜头保持原有建筑直连，重开后读取新的玻璃；本次不保存或改动总镜头文件，也不操作当前连接的其他项目。背景立面因复用同一门窗集合而自动继承此次材质替换。

- [修改前](transom_before.png)
- [修改后](transom_after.png)
- [完整教室镜头](classroom_after.png)
- [发布与重开验证](published.json)
- [对象修改明细](changes.json)

评审使用当前总镜头的光照与色彩管理，Cycles / OptiX、48 samples；侧面评审为临时正交机位，未写入工程。上亮窗已可透见走廊外侧窗框。整体色彩、窗帘、家具及主相机沿用当前工程。

备份与原文件哈希：`07_pipeline/cache/transom_glass_20260919/inputs.json`。恢复建筑时，将该清单中的 `environment_before.blend` 复制回清单内的正式 `path`，相对贴图路径以正式位置为基准。

保留现有对象名称供场景追踪；名称中的旧 `blue upper infill` 不再表示实际材质类型。当前实际绑定是透明玻璃。
