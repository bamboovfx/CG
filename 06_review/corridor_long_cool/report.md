# 走廊延长与冷色墙面 · 2026-09-17

依据用户提供的三张 breakdown 截图：第一张用于观察最终气氛，第二张用于墙面色彩，第三张用于门窗与柱网的重复关系。参考截图归档于 `01_preproduction/references/corridor_breakdown_20260917`，为原片参考，非自制或 CC0 素材。

走廊从 10.5 m 延长至 42 m，Y=-5.95..36.05；此长度是制作设定，非原片实测尺寸。保持原横向位置和宽度。外窗使用十二组独立窗组，教室侧延伸三组既有门窗，并补齐邻室地面、顶面、外窗及隔墙。前后均有实体收口，旧短走廊保留但禁用。

墙面采用浅冷灰上墙、低饱和灰蓝墙裙。独立复制材质，保留已有纹理明暗、粗糙度和法线。原教室共用墙面只增加走廊侧覆面，不改教室侧材质。没有将参考第一张的滤镜直接施加到整个镜头。保留现有世界灯光、曝光与主相机；因此教室仍呈暖色，走廊的光影并非原片逐像素复刻。

评审图使用 Cycles / OptiX，1600×675、48 samples。前后共 18 条长轴检查射线到达两端，无旧短走廊端墙阻挡；候选中原有本地对象变换保持不变，外部图片依赖检查通过。发布结果见 `published.json`。

- 建筑源：`02_assets/work/classroom_environment.blend`
- 总镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 新评审相机：`cam_corridor_long_review`；活动主相机不变。
- 恢复副本：`07_pipeline/cache/corridor_long_cool_20260917/environment_before.blend` 和 `shot_before.blend`。副本按原源目录的相对引用保存，恢复时放回原目录。

![走廊](corridor.png)

![教室主镜头](classroom.png)
