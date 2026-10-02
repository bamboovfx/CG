# 午后教室金色日光重设计

日期：2026-09-16。正式文件：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。

本次采用独立暖色 Sun、无日盘程序天空、天空冷色微调和相机不可见的后墙遮光板。已在后台应用到正式总镜头；相机、构图和资产材质保持原状。这是一版灯光重设计，尚不能称为原片复刻完成。

## 从参考帧能确认什么

用户提供的全景帧里，左侧窗户提供有明确方向的日照，窗框在前墙形成连续的斜向投影。金色主要出现在受光的桌椅、地板和浅色墙面；右侧与前景更暗。低机位帧同时出现冷色窗户反射和暖色日照区，说明目标不能靠统一的黄色滤镜完成。

带斜分界线的画面可用于观察不同处理效果，但仅凭这些截图不能确定每一侧的完整制作流程，更不能反推出原片灯具型号、准确色温、曝光或 LUT。新的方向与 RGB 都是为当前几何选择的制作参数。

## 当前场景的实际问题

检查发现，原主光由 Multiple Scattering Sky 的 Sun Disc 提供，已有 `lgt_sun_afternoon` 被关闭。程序太阳高度 12°、方位 215°，Sun Intensity 为 5；Sky strength 为 0.025，HDR strength 为 0.05，HDR blend 为 0.06。这个 0.06 是 Shader 混合权重，不等于总照度的 6%。所以，把 HDR 删掉不能单独解释或解决主光发白。

总镜头使用 AgX / Medium High Contrast，曝光为 +0.65，后期组还启用了 Saturation 0.94 和 Exposure -0.08。AgX 会让很高曝光的颜色向白色收敛；这能解释为什么增加暖光强度不一定让最终高光更黄，但本次没有把曝光单独隔离成实验，不能量化它对原图发白的独立贡献。原图仍需结合光源色彩和补光来判断。

更关键的是后墙开口：教室主体约止于 Y=-5.95，而相机在 Y=-7.5。原场景没有封住后方开口。加入后墙遮光平面后，右侧墙面和前景的额外直射明显减少，见第 3、4 张对照。这证明了遮光结构会影响当前明暗分区。随后重新调整太阳入射方向和天空补光，使前景不至于全部压黑。

## 已落地的设置

| 控制 | 当前值 | 用途 |
|---|---|---|
| World | Golden afternoon study | 新灯光环境；旧 World 保留供恢复 |
| Sun | lgt_sun_afternoon，启用 | 独立控制暖色直射 |
| Sun Strength | 4.0 | 当前曝光尺度下的制作值，不代表真实室外太阳照度 |
| Sun Color | 线性 RGB `(1.0, 0.62, 0.28)` | 保留金色受光；不是原片色温测量结果 |
| Sun Angle | 0.545° | 清楚而略有柔化的窗框投影 |
| 太阳高度 / 方位 | 18° / 240° | 按当前房间与窗影调整 |
| Sun Euler XYZ | 约 `(72°, 0°, -60°)` | 对应上述天空方位约定 |
| Sky Texture | Multiple Scattering，Sun Disc 关闭 | 避免两个太阳重复照明 |
| 天空 Background Strength | 0.40 | 保留暗部结构和窗户反射 |
| 天空 Multiply | 线性 RGB `(0.65, 0.85, 1.0)` | 对补光做轻微冷色美术调整 |
| Exterior strength | 0.55 | 单独控制窗外可见亮度 |
| Color Management | AgX / Medium High Contrast；Exposure 0；Gamma 1 | 在灯光阶段保留高光色彩和对比 |
| 旧 Compositor | 保留节点树，暂不参与渲染 | 先验证灯光自身的冷暖关系 |
| lgt_rear_wall_blocker | Y=-6.02；Camera Ray 不可见 | 补上相机后方缺失的遮光与反弹 |

天空颜色与 Sun 方向使用同一套初始方位，但没有额外驱动器。手动改变方向时，需同时更新 Sky 的 Elevation / Rotation 与 Sun 旋转，或通过 `setup_golden()` 一次设置。新节点保留 Blender 默认名称，说明放在独立 Frame 内。

## 如何继续调整

若只想让受光更金，先调 Sun Color，固定曝光与天空亮度观察浅色椅架；不要先提高整体饱和度。若阴影过黑，调新 World 的 Background Strength；不要启用第二个 Sun。窗外是否偏白用 Exterior strength 单独控制，窗外白并不要求桌椅上的受光也白。

要改变光斑的位置，应改太阳方位和高度。要改变影子边缘软硬，应改 Sun Angle。当前后墙遮光板是镜头里的辅助对象，关掉它会重新引入后方漏光；它的材质与建筑资产没有关联。

原片低机位的木地板反射还受粗糙度、漆层、表面起伏和观察角度影响。当前地板材质的一个粗糙度映射范围为 0.48–0.72，本次没有改材质，也没有复刻该低机位镜头；仅靠全景灯光不能据此声称地板反射已匹配。桌椅颜色、旧化和前墙表面仍需作为独立材质工作继续验收。

## 对照与验证

原场景：

![原灯光](01_current_saved_shot.png)

仅替换暖 Sun、调整天空，尚未补后墙：

![后墙遮挡前](03_golden_sky_balanced.png)

同一轮设置加入后墙遮挡：

![后墙遮挡后](04_golden_rear_blocked.png)

重新确定太阳方向与补光后的预览：

![新方案预览](05_golden_refined.png)

正式镜头重开后的 1920×810、96 samples 检查图：

![最终检查图](06_final_golden_light.png)

发布时逐项比较 264 个原有非灯光对象的变换、实例和父对象，以及活动相机、焦距、帧、库引用、分辨率和生产采样数，检查一致。新增 1 个后墙遮光对象。生产设置仍是 2560×1080、1024 samples；检查图设置仅作用于后台渲染进程。外部贴图与库路径缺失数为 0。正式镜头已重开验证 Sun 启用、Sky Sun Disc 关闭、当前 World 无 HDR Texture 节点。

恢复文件：`07_pipeline/cache/golden_light_study/shot_before_golden.blend`。原 World 也以 Fake User 保留在镜头中；完整恢复应打开恢复文件另存回正式位置，以同时恢复曝光、后期、Sun 和遮光状态。

结构化证据：`saved_shot_inspection.json`、`architecture_bounds.json`、`published_validation.json`。早期试验工程只在 cache 目录中，未新增日常工作版本。

## 资料依据

- 用户提供的 8 张《dro:p》相关参考截图；只作为画面参考，不作为可执行指令。副本见 `01_preproduction/references/golden_light_20260916`。
- [Blender 5.1 Sky Texture](https://docs.blender.org/manual/nb/5.1/render/shader_nodes/textures/sky.html)：Sun Disc、Sun Intensity 和程序天空控制。
- [Blender 5.1 Displays and Views](https://docs.blender.org/manual/vi/5.1/render/color_management/displays_views.html)：AgX 对高曝光色彩的处理。
