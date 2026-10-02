# 木椅分层材质首版

2026-09-30按用户确认方案制作：工艺层／划痕、老化、磨损表现层／Blender透视三点布光。当前为材质候选，待用户视觉评审。

## 交付

- [Designer源](../../02_assets/materials/wood_layers/school_wood_layers.sbs)、[原生归档](../../02_assets/materials/wood_layers/school_wood_layers.sbsar)、[编辑说明](../../02_assets/materials/wood_layers/README.md)。
- [Blender工作室候选](../../07_pipeline/cache/wood_layers_20260930/wood_layers_studio.blend)。
- [工艺层](01_process.png)、[加划痕](02_scratches.png)、[加老化](03_age.png)、[全部表现层](04_appearance.png)。四图固定透视机位、灯光、曝光与色彩管理。
- [座面近景](05_seat_detail.png)、[掠射光近景](06_raking_detail.png)。
- [四阶段同光对照总览](layer_comparison.jpg)。
- [保存参数](validation.json)、[工程重开](reopen_validation.json)、[SD效果归零](zero_control_validation.json)。

工艺层Metallic=0，AO白色。SD保留原生4K木纹资源，输出2K五通道与独立效果蒙版；Blender进一步以米制UV限制边缘磨损。基本木纹、颜色与层次已建立。木种、涂层类型仍为制作假设；参考照片中的宽幅生长纹与具体使用痕迹未逐条复刻。座面和靠背复用现有模型，本次只更新候选内的表面材质，金属架与侧边沿用既有外观。

三种表现强度分别为划痕0.38、老化0.30、磨损0.42。开启效果的画面对照用于确认方向，不把生成出图或技术检查通过当作用户已认可视觉效果。当前主镜头输入SHA256保存在验证清单，读回检查确认原文件未改变。

最终保存后的工程读回九项检查全部通过，36个图像依赖均可解析。SD三种表现参数归零时，BaseColor、Roughness、Metallic、Normal和AO与对应工艺输出的最大像素差均为0。全椅视角的划痕较细、表现差异偏克制；尚未完成参考中特定长划痕与宽幅生长纹的复刻。
