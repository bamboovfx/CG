# Tripo木椅：加强老化与磨损

2026-09-30。用户认可现有工艺层，要求表现层的颜色变化和凹凸更明显。新版从用户最近保存的木椅候选加载，只替换表现组，另存[可编辑工程](../../07_pipeline/cache/tripo_wood_appearance_20260930/tripo_wood_appearance.blend)。

![同光前后对照](appearance_comparison.jpg)

旧版老化主要是低强度棕色混合，凹凸只有划痕；磨损范围很窄。新版加入局部褪色、涂层发暗与破损，磨损贴合Tripo木板的实际圆角轮廓，并分布到座面前缘、接触区和背板边缘。露木颜色保留木纹，损伤边界沿木纤维破碎；长划痕增加可读性，短划痕保持低对比。

使用同机位、同灯光、同曝光比较。已检查[整体](04_after_whole.png)、[座面](03_after_seat.png)、[靠背](05_after_back.png)、[高光前后](highlight_comparison.jpg)和[工艺／老化／磨损隔离](appearance_isolation.jpg)。高光诊断使用12W条形主光，前后两张条件完全相同；保存工程恢复原55W主光和原三点布光。

## 可编辑入口

选中 `LP_part_02` 座面或 `LP_part_09` 靠背，在各自 `Reference wood / seat`、`Reference wood / back` 材质内选择默认名称 `Group.001`。当前表现强度为 Scratches=0.95、Age=0.72、Wear=0.88；三个参数独立，归零恢复工艺层。默认节点名称／标题保留，解释放在注释框。原工艺组和已打包的imagegen木纹保持。

老化、磨损、划痕分别使用120／220／100微米的最大凹槽距离，当前强度会继续缩放这些高度。它们是局部着色凹凸，不改变几何轮廓。完整涂层仍使用原顺纹微法线；损伤区同时影响Base Color、Roughness、基础Normal、Coat Normal和Coat Weight。Metallic继续来自工艺层的零值图。浅表损伤没有另外烘入黑色AO。

原生SD表现配方为[座面](../../02_assets/materials/tripo_wood_appearance/wood_appearance_seat.sbs)、[背板](../../02_assets/materials/tripo_wood_appearance/wood_appearance_back.sbs)，各有SBSAR和4K输出。原始技术蒙版以2K生成，SD输出4K；不宣称新增4K纹理细节。`Raw_*` 输出供Blender组内按上述参数实时控制，其余输出是SD已经乘强度的版本，避免再乘一次。工艺层继续使用上一版imagegen生成的底纹，本轮没有重新生成或修改它。

## 验证

- [重开记录](reopen_validation.json)：17项检查通过；两块木板绑定、三层凹凸、基础／清漆接线、透视相机和原三点布光正确，28张实际使用图像已打包，颜色空间正确。
- [工艺保护与SD归零](sd_validation.json)：12张原工艺文件SHA256保持；两套SD的8个表现输出归零后最大像素值均为0。工艺归零渲染按8位读回的最大像素差1，平均差0.0000497，无大于2的差值，来自法线运算浮点精度。
- [源与工程保护](validation.json)：最新输入SHA256 `bb4c39882d02c5f175b605754673de71135c9a9a1d504db2bef0c7adb8ee58e8` 保持。两块木板的顶点／三角面／原UV／自定义法线摘要，以及原工艺节点、参数、接线和打包图像摘要均保持。

技术检查通过，新版表现层待用户视觉评审。当前磨损明显加强；与原照片的损伤位置、形状不视为逐处复刻。
