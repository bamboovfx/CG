# Tripo木椅：扫描辅助表现层重制

2026-09-30。用户指出上一版表现层细节精度低、颜色变化过于简单。本轮撤掉规则浅色条带，以真实木桌材质的颜色／反射／高度细节参与制作；保留已认可的imagegen工艺层。可编辑候选：[tripo_wood_detail.blend](../../07_pipeline/cache/tripo_wood_detail_20260930/tripo_wood_detail.blend)。

![前后同光比较](appearance_comparison.jpg)

## 参考研究与实际采用

用户原课椅照片继续决定蜜色、宽幅生长纹、长划伤与损伤分布，工作室桌面照片决定整体平整与微妙反射。另逐图研究三份原始材质：

| 参考 | 观察重点 | 本轮用途 |
|---|---|---|
| [Wood Table Worn](https://polyhaven.com/a/wood_table_worn) | 浅深褐色、擦伤、细小嵌色、磨耗与粗糙度变化 | 原生8192×8192 Diffuse、Rough、Displacement作为SD输入；摄影Dimitrios Savva、处理Rico Cilliers |
| [Wood Table Large](https://polyhaven.com/a/wood_table_large) | 旧涂层色差、小磕碰和暗色损伤边缘 | 观察不同尺度损伤的组织；拼板接缝不移植到椅面 |
| [Wood Table 001](https://polyhaven.com/a/wood_table_001) | 完整涂层下的细纤维及平整感 | 比较完整区域与磨耗区域的反射关系 |

![三份原始资产研究](reference_study.jpg)

以上下载的是公开原始资产图，许可为[Poly Haven CC0](https://polyhaven.com/license)，没有下载或移用网站示例渲染。实际下载规格、URL、MD5、SHA256与像素尺寸见[来源清单](../../02_assets/textures/external/polyhaven_wood_detail/manifest.json)。参考照片没有作为可分发材质贴图。

## 这次改变了什么

上一版用低分辨率结构场放大后着色，色彩目标多为常量，短划痕与露木形状缺少差别。新版把“在哪发生”与“发生区域内是什么细节”分开：位置包络、稀疏边缘磕碰与定向长划痕直接在4096采样；真实扫描提供细碎颜色、粗糙度和高度变化。扫描色图按逐RGB通道调整到现有蜜色范围，老化、露木、嵌色各保留完整色图，不再以三个常量色代表整个表面。

长划痕有渐细的沟槽、微弯曲和单侧掀起纤维，沟槽深色与纤维浅色分别控制。前缘采用毫米级间断磕碰和局部擦伤，替换上一版大块浅色条带。整体保留宽幅工艺木纹，完整涂层区域保持原微法线；表现高度只在对应蒙版内叠加。

![实物尺度特写前后](macro_comparison.jpg)

[接触区1800像素特写](06_contact_macro.png)、[划痕1800像素特写](07_scratch_macro.png)、[整椅](04_detail_whole.png)、[靠背](05_detail_back.png)、[条形光高光](08_detail_highlight.png)、[独立效果](effect_isolation.jpg)。特写使用96样本和相同AgX／曝光，比较图两边相同机位、灯光和样本数。

![实际SD输出1:1裁片](map_100_percent.jpg)

裁片是512×512原像素，无放大，座面宽37.1cm时对应约46mm。实际源为8192，SD输出4096；扫描裁取范围按板宽约37cm、背板高度约19cm适配。源像素实际提供的细节密度、局部裁取和滤波仍决定精度，不把导出4096视为视觉达标。保留的工艺底纹源仍是此前imagegen生成的约1254像素图，本轮没有改它；表现扫描增加独立细节，不能把整套工艺宣称为原生4K。

## 可编辑源与参数

- 原生SD：[座面](../../02_assets/materials/tripo_wood_detail/wood_detail_seat.sbs)、[背板](../../02_assets/materials/tripo_wood_detail/wood_detail_back.sbs)，同目录有SBSAR。原始扫描资源在SBSAR内烹制，SBS仍引用项目内原始资源。
- 生成器：[SD结构与配方](../../07_pipeline/scripts/tripo_wood_detail_sd.py)、[Blender应用与渲染](../../07_pipeline/scripts/tripo_wood_detail_blender.py)。
- Blender：选 `LP_part_02` 座面或 `LP_part_09` 靠背，在对应材质默认节点 `Group.001` 中调 Scratches=0.95、Age=1.0、Wear=0.95。默认节点名／标题保留，说明放在注释框。
- SD配方的初始默认值为0.85／0.70／0.80；导出五通道时已明确覆盖为最终0.95／1.0／0.95，实际导出值记录在[纹理清单](../../02_assets/textures/generated/tripo_wood_detail/manifest.json)。`Raw_*` 图未乘强度，供Blender组实时控制；BaseColor、Roughness、Normal、Metallic、AO为参数化SD导出。

四个Bump距离标尺为120／220／100／30微米，分别用于扫描旧漆、露木、沟槽、掀起纤维；实际起伏再乘高度信号和位置强度，不能把标尺当作每处实际损伤深度。扫描高度没有已验证的绝对毫米标定，本轮按抛光木材参考人工校准。Blender使用实时四层Bump和独立清漆粗糙度，SD输出采用高度转OpenGL法线和切线法线合成，两条着色路径不宣称逐像素相同。

## 验证与状态

[工程重开](reopen_validation.json)19项通过：36张实际使用图像打包、颜色空间正确、两块木板三份真实色图与四层凹凸接入、基础与清漆法线／粗糙度接线正确，原三点布光和透视相机保留。[输入保护](validation.json)记录原候选SHA256保持，两块木板顶点／面／原UV／自定义法线以及工艺节点、参数、接线、打包工艺图像摘要保持。

[SD与工艺验证](sd_validation.json)：12张原工艺文件哈希保持；两套SD表现高度归零后为恒定中性平面，Metallic全图为0；新增高度、蒙版、沟槽和纤维图有实际4K信号。关闭表现的模型前后渲染最大差为1个8位值，平均差0.0000559，无超过2的差值。

技术检查通过，视觉仍待用户评审。本轮提供更细的扫描辅助表现及100%证据；与原椅照片的每处伤痕、木种和材质色层没有宣称完全一致。
