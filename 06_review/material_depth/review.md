# 教室材质与结构细化 · 2026-09-12

本轮针对讲台掉漆、墙面粉刷、公告贴墙、粉笔灰、教师桌和挂钟做了实物参考与近景检查。制作设定和原片还原度分开记录；以下图像用于本轮视觉复核，不代表整段短片已完成复刻。

| 部位 | 实际修改 | 检查结果 |
|---|---|---|
| 讲台三块白色面板 | 连续腐蚀场同时控制颜色、裸钢、粗糙度及真实置换；约 0.36 mm 漆层与 0.4 mm 起翘，细分后边长约 0.55 mm；细锈坑、橘皮漆面和下部污迹过渡 | 三个材质输出均连接 Displacement，模式为 Displacement and Bump；微距可见漆边和凹陷，不再只有棕色图案 |
| 白墙与绿墙 | 实拍 4K 灰泥高度、粗糙度，按原始 2 m 尺度映射；分开控制毫米级墙体起伏和更细的刷痕、颗粒 | 在原场景日光下检查白墙与阴影边缘；绿墙减小高度以避免外墙式粗糙 |
| 公告纸 | 0.16 mm 厚度；表面离原墙平面约 1.8–5.8 mm；上角贴近墙面，底角轻翘；纸纤维凹凸与细微颜色变化；针杆伸入墙面 | 消除原先约 5–8 cm 的悬空间隙；两张过宽公告缩窄 6%，消除相交边缘 |
| 黑板木框和粉笔槽 | 保留课桌同源木纹；木框下部有不均匀粉灰，槽底补独立薄粉层与细颗粒 | 在斜视近景检查木纹、擦抹和槽底积灰 |
| 讲台右侧小桌 | 替换为教室现用 `AST_school_desk_HP`，复用其钢管、托斗、卷边、螺钉、锈蚀与脚套 | 开口方向为世界 +Y，面向黑板；脚底与现有课桌保持同一高度 |
| 挂钟 | 重建旋压外壳、卷边框、内圈、密封圈、2 mm 弧面玻璃、薄表盘、秒针、固定螺钉及墙垫 | 贴墙后为避开顶梁，整体下移 50 mm、左移 20 mm；与梁下沿间隙约 13 mm |

相机、当前帧和其他实例变换保持本轮开始时的现场状态。发布时重新载入资产库并合并教师桌替换，不用后台镜头文件覆盖用户正在打开的场景。

## 实物资料

[参考来源与观察](D:/00_projects/10_CG/Shot_Test/06_review/material_depth/references.md) · [4K 纹理来源、许可与哈希](D:/00_projects/10_CG/Shot_Test/06_review/material_depth/textures.json)

白墙使用 [Poly Haven / Amal Kumar 的 Painted Plaster Wall](https://polyhaven.com/a/painted_plaster_wall)，保留原始文件名和 CC0 来源。未将腐蚀、纸张或钟表的参考照片直接贴到资产上。

## 原场景灯光下的近景

讲台下沿：真实漆层边缘、暗色锈坑、少量露钢和完整漆面。

![讲台腐蚀近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/rust_v3.png)

白墙：粉刷颗粒和抹灰起伏。

![白墙近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/wall_v2.png)

公告：纤维表面，边缘不再相互穿插。

![公告纸近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/paper_macro_v3.png)

挂钟：壳体、玻璃和表盘的实际层次。

![挂钟近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/clock_v2.png)

粉笔槽：下框磨损和积灰。

![粉笔槽近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/chalk_v4.png)

替换课桌：从黑板一侧观察托斗开口。该图为第一轮方向检查，背景讲台材质以最终腐蚀近景为准。

![替换后的课桌](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/teacher.png)

## 整景

![整景 1920×810](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/material_depth/v001/scene_v4.png)

## 文件

- 当前镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 同步资产：`02_assets/library/classroom_assets.blend` 及教学道具、设备、教室壳体、走廊四个源工程。
- 可恢复备份：`07_pipeline/cache/material_depth/shot_before.blend`，引用同目录的旧资产库；另保留开始时和发布前的现场副本。
- 技术检查：`06_review/material_depth/validation.json`；检查外部图片路径、置换连接、纸张间距、钟表避梁、课桌方向及相机保持情况。

真实置换在 Cycles 渲染和渲染预览中显示；Solid 模式不计算材质输出的置换。
