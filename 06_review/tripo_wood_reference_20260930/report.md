# Tripo木材参考返工 · 2026-09-30

材质已经应用到现有Tripo课椅的座板与靠背，采用 `tripo_chair_material_v2_20260930/chair_material_v2_baked.blend` 作为几何输入。保留26个Tripo部件、原UV、固定三角化和导入自定义法线；五金外观沿用输入。主教室镜头及输入候选没有被覆盖。

## 交付

- [可编辑Blender工程](../../07_pipeline/cache/tripo_wood_reference_20260930/tripo_wood_reference.blend)。木板内工艺层和表现层分开，划痕／老化／磨损各自可控，纹理依赖打包。
- [SD座板源](../../02_assets/materials/tripo_wood_reference/reference_wood_seat.sbs)、[背板源](../../02_assets/materials/tripo_wood_reference/reference_wood_back.sbs)、[编辑与来源说明](../../02_assets/materials/tripo_wood_reference/README.md)。
- [整体](02_final.png)、[座面](03_seat_detail.png)、[前背板](04_back_detail.png)、[后背板](05_rear_detail.png)、[掠射光](06_raking.png)、[条形光](09_highlight_close.png)。
- [材质参考与前后对照](reference_comparison.jpg)、[高光参考与修正对照](highlight_comparison.jpg)。
- [高光通道隔离](channel_isolation.jpg)：同底色、同光、同机位、同曝光分别比较平法线／恒定粗糙度、仅变化粗糙度、变化粗糙度加微法线，避免用色彩和布光改动冒充法线修正效果。
- [几何保护和保存清单](validation.json)、[工程重开](reopen_validation.json)、[SD全图与表现归零](sd_validation.json)。

## 外观依据

用户原课椅参考约束蜜色涂层、自然宽幅弧线、细纤维、座面长划痕、局部窄边露木。数学年轮初次试验过于规则，已换为内置imagegen按参考生成的自然木纹基础图，再通过SD制作五通道；划痕与旧化保留为独立蒙版。生成原图1254²，通道计算输出4096²。提示词、项目内源图及哈希完整保留，未直接投射实物照片。

用户补充的工作室木桌照片只约束高光：整体抛光平整，高光保持连续，但木纹微孔、细擦痕及涂层变化造成微妙的亮度和边缘变化；没有借用工作室桌子的浅色配色。

## 高光修正

用户指出平板高光后，实际读图测得旧粗糙度约0.386–0.393，微法线RG范围127–128，工艺高度范围约0.2微米；真实工程的Normal与Roughness已连接，但变化近乎为零。Coat Normal与Coat Roughness此前没有显式连线。

现改为从自然木纹分离高频顺纹结构，微孔高度完整范围约22微米，粗糙度采用相同结构加轻微涂层变化；Normal、Roughness与清漆对应通道明确连接，数据图为Non-Color，切线法线和材质坐标同用 `UV_WoodReference`。法线参数强度为1，幅度由有物理尺度的高度控制。BaseColor不含灯光或AO。

实际全图范围和标准差见 `sd_validation.json`；工程读回记录包括真实接线、法线UV、色彩空间、材质绑定和输入几何哈希。固定三点灯、AgX、1400²、64samples完成同光对照；条形光和掠射光另用于诊断，不作为模型新凹槽。

最终工程重开13项检查通过，30个使用中图像依赖全部可解析，26个Tripo部件保留。原输入文件与木板顶点／三角面／导入UV／自定义法线哈希均一致；所有材料数据依赖打包，无缺图。

最终座面工艺粗糙度约0.354–0.440，标准差0.024；工艺法线RG112–143，实际典型变化远小于极值。两套SD表现参数归零时五通道最大像素差均为0，全图Metallic=0。靠背宽纹已校正为横向走势。上述检查对应最终保存版本。

## 评审范围

宽纹、蜜色涂层、使用划痕和微细反射已按两组实物参考重制。逐处木纤维、具体划痕和无法辨认的背面印记没有宣称像素复刻；Tripo既有板厚、表面形状与五金磨损保留，不能用材质消除几何差异。当前交付待用户视觉评审，技术通过不代表用户已经认可完全一致。
