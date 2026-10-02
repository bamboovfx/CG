# 走廊、外窗与地板日照修正 · 2026-09-17

已覆盖建筑源，并通过 MCP 更新当前打开的总镜头、保存用户实时编辑。后台重新打开已发布工程检查通过。

## 原因与修改

1. 原走廊是 42 m 的未完成延伸段，近端完全敞开，远端只有透光玻璃。当前收为紧贴这间教室的 10.5 m 走廊段，前后均加实体墙、墙裙和踢脚线；外侧保留自然采光窗。旧延伸段保留但停用，可恢复。
2. 原外窗每 1.1 m 连续排窗扇，墙柱却是另一套不均匀间距，中柱宽达 0.6 m，造成窗框被柱子截断。现在按三个柱间独立制作完整窗组：每组四扇双轨推拉窗，上部独立亮窗，并有玻璃压条、胶条、拉手、锁扣和排水槽。中柱调整为 0.22 m，第三帘束随柱移动。
3. 原窗台与下框较高，当前下墙 0.855 m，窗台顶约 0.91 m，主横档 2.65 m。玻璃仍从窗框内起算，不把下墙改成透光面。
4. 实时镜头已被用户改成三节点程序天空，独立 Sun 已删除。本次保留这套世界节点。原天空太阳高度 10°、旋转约 215°，光线偏向从后墙方向进入，部分地板位置无法沿直线看到左窗。调整为高度 16.5°、旋转 250°，让光线更侧向穿过窗洞；曝光从 0 调至 -0.65 EV，保留亮部颜色。未给地板增加自发光或局部补光灯。
5. 图中左侧三个小块实际是窗外背景楼的占位模型，不属于走廊。已归入 `AST_classroom_shell / Background school silhouettes`，保留原位置与渲染贡献。

## 参考依据

- 用户提供的 dro:p 画面：窗柱节奏、上亮窗、侧向日照及地板长条投影是主要画面依据。
- [越後屋神立小学校实物平面](https://www.echigoyastudio.jp/pdf/Kandatsu.pdf)：参考教室与走廊并列、共用分隔墙的空间关系。
- [YKK AP 学校窗改修资料](https://www.ykkap.co.jp/business/building/kaisou/school/)与 [LIXIL 学校推拉窗产品说明](https://www1.lixil.co.jp/design_award/product/780)：参考学校窗组与推拉开启的构造类别。

新窗洞宽度、窗台标高与 10.5 m 封闭段长度均为本镜头的制作设定，不声称是原片实测数据，也不代表整栋真实学校的完整交通组织。

## 验证

- 当前走廊可见网格范围：X=4.0..6.785 m，Y=-6.13..4.73 m（包含墙体与窗台），未进入教室内部核心区。
- 从走廊内向前后端墙发出的 18 条检查射线，全部命中实体墙或墙裙。
- 地板 1050 个规则抽样位置中，151 个能沿太阳方向穿过玻璃直接见到天空；墙体、窗框、窗帘和家具仍正常挡光。这是离散几何检查，不是地面照度计算。
- 四个角度完成 Cycles / OptiX 渲染：主镜头、低机位地板、走廊端墙、窗户正侧视。外立面检查图单独使用 -2 EV 室外评审曝光，正式镜头保持 -0.65 EV。
- 总镜头中 268 个已有本地对象变换前后逐项一致，活动相机仍是 `cam_sh010_main`。重开已发布文件后未发现缺失贴图/引用。

## 文件

- 建筑源：`02_assets/work/classroom_environment.blend`
- 总镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 新检查相机：`cam_floor_light`、`cam_corridor_check`、`cam_windows_side`
- 恢复目录：`07_pipeline/cache/corridor_window_repair_20260917`；其中 `environment_before.blend` 为建筑修改前副本，`shot_live_immediately_before_update.blend` 保留应用修改前最后一次实时总镜头状态。
- 验证记录：`validation_published.json`、`source_published.json`、`live_published.json`。

![主镜头与地板日光](D:/00_projects/10_CG/Shot_Test/06_review/corridor_window_repair/05_front_final.png)

![低机位日光检查](D:/00_projects/10_CG/Shot_Test/06_review/corridor_window_repair/06_floor_final.png)

![走廊与实体封口](D:/00_projects/10_CG/Shot_Test/06_review/corridor_window_repair/07_corridor_final.png)

![三个独立窗组](D:/00_projects/10_CG/Shot_Test/06_review/corridor_window_repair/08_window_final.png)
