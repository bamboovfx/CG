# 椅子金属工艺层／表现层 — 2026-10-01

按用户要求沿用木材分层方式，完成Tripo课椅的11个涂漆部件和12个深色螺钉。已应用并原位保存到[当前工作文件](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)；[独立候选](../../07_pipeline/cache/chair_metal_layers_20261001/chair_metal_layers.blend)保留作评审。正式教室镜头未修改。

工艺层是钢基底、灰白涂漆及细微涂层反射，螺钉为深色氧化工艺变体。表现层按参考安排上横管长条间断剥漆、局部磕碰、连接与近地锈蚀、漆面雾化、浅划痕和稀疏附着物；上横管以深褐氧化为主，其它损伤保留赭色细节与钢灰露底。

Wear／Rust／Age／Scratches／Dirt分别控制，多通道共用对应蒙版。掉漆同时改变颜色、粗糙度、金属性、75µm浅台阶与涂层覆盖。锈控制颜色／粗糙度／微孔法线，完整漆与锈为非金属，露钢为金属；过渡边界采用滤波与强度混合。

内容为原生Designer配方，77个节点、21张4K输出，包括工艺通道、表现内容及完整SD平铺样片。实物锈细节采用[Poly Haven Rust Coarse 01](https://polyhaven.com/a/rust_coarse_01)原始8K颜色／粗糙度／位移，许可[CC0](https://polyhaven.com/license)；高通分离并重映射微细内容，没有复制扫描物体的宏观形状。[原生SBS](../../02_assets/materials/chair_metal_layers/chair_metal_layers.sbs)、[SBSAR](../../02_assets/materials/chair_metal_layers/chair_metal_layers.sbsar)、[用法](../../02_assets/materials/chair_metal_layers/README.md)。

材质使用每部件绑定的本地位置还原原装配米制坐标，再显式三向投射；移动或旋转部件后损伤不在表面滑动。原几何、全部UV与自定义法线保留。Blender通过物理高度生成三向映射法线，并连接到基础和涂层Normal；OpenGL切线法线另供常规UV使用。

实际检查：候选与保存的当前文件重开，各54项通过，包括23部件绑定、12张实际使用4K图打包和色彩空间、真实多通道接线、几何／UV／法线、木材根树／组、胶脚和印记清理保护。实时应用前再次备份并保留当前编辑、Plane选择与OBJECT模式。[候选检查](candidate_reopen_validation.json)、[当前文件检查](current_reopen_validation.json)、[实时应用记录](applied.json)、[保护摘要](validation.json)。

保持原三点布光／色彩管理，以64spp固定种子和透视机位检查整椅、上横管、下部连接、背面。全部表现归零与直接接工艺输出的同光图最大差1个8位值，平均差0.00003864，大于2的差异为0：[Blender归零](zero_comparison.json)。原生SBSAR五个强度归零亦按4K输出核对：[SD归零](sd_zero_validation.json)。

![原材质／分层材质](whole_comparison.jpg)

![上横管工艺／表现对比](rail_comparison.jpg)

![管脚与连接近景](03_after_foot.png)

![原生通道100%裁片](map_100_percent.png)

技术制作与实际应用完成；视觉状态为review，参考接近程度待用户评审。位置按当前Tripo形状适配，未改变其形状以强行拟合照片。当前木材外观保持。
