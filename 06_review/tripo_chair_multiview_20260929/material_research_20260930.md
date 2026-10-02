# Tripo 课椅材质重制依据 · 2026-09-30

## 判断与参考优先级

本次只以用户提供的[原片画面](../../01_preproduction/references/film/drop_user_reference_clear.png)确定镜头里椅子的总体明暗，以 AITA 出售的**实物椅照片**确定座板、靠背、钢管和脚套表面；不以任何旧 Blender 椅模型或旧渲染作外观依据。椅子的 Tripo 网格只用作当前待制材对象。AITA [原商品页](https://aita.ocnk.net/product/3087)说明它是有伤痕、污垢和锈的旧学校桌椅，且卖家明确提示照片存在色差。以下数值只是中性照明下的制材起点，不是从照片测出的反射率或标准色。

本地实物图：

- [座板顶面、背板背面、管架及横撑](../../01_preproduction/references/props/20160220_201e63.JPG)：座板是暖蜜橙色、连续的宽窄相间弯曲木纹；背板背面纹理更细、总体更平直。光滑清漆仍覆盖大部分木面；细划痕和小色斑存在，但没有通体粗糙黑点。背框上横管和低位横撑掉漆明显，大片管身仍是完整的浅象牙色漆。背板可见黑色固定点与银灰色托片，脚帽偏黄。
- [椅子与课桌同框](../../01_preproduction/references/props/20160220_47c158.JPG)、[侧后视角](../../01_preproduction/references/props/props_01.jpg)：椅子木板比桌面更暖、更黄；桌面偏粉灰木纹，不能把桌面贴图直接当成椅子木板。脚帽与管架明度、表面光泽也不同。
- 照片均来自 [AITA 商品页](https://aita.ocnk.net/product/3087)，本地来源和 SHA256 见 [`school_desk_reference_manifest.json`](../../01_preproduction/references/props/school_desk_reference_manifest.json)。照片版权未获再分发授权；只作观察依据，不裁剪、投射或采样成资产贴图。

同类制造工艺有厂商旁证，但**不能据此断定这把旧椅的木种、漆配方或脚帽材质**：NOVATRONIC 的[学生椅](https://schola.novatronic.cz/en/student-chair-2)使用清漆成型榉木胶合板、粉末涂装钢架和塑料脚垫；[Virco 产品目录](https://virco.com/wp-content/uploads/2026-Factory-Price-List-3.26.26.pdf)亦区分胶合板座/背、钢管架、粉末涂层及尼龙脚垫。用这些资料建立板材/涂层/裸钢/脚帽四类表面，不套用厂商照片的颜色或造型。

## 建议的材质层与调参起点

| 区域 | 先制作的表面层 | 初始 PBR 范围与观察标准 |
| --- | --- | --- |
| 座板、靠背正反面 | 胶合板面皮的长向木纹 → 暖色透明清漆 → 少量划痕/压痕/漆面擦亮 | 木材与清漆均为非金属，Metallic=0；清漆主反射 Roughness **0.28–0.42**，局部摩擦面可降至约 0.24，深划痕/污迹升至约 0.5。色相起点为暖黄橙，座面可有缓慢变化的宽幅弯曲木纹；背板用更细、更安静的纹路。不能靠高频颜色噪点模拟木孔。以上粗糙度是美术起点。 |
| 板材侧边 | 独立薄侧边面皮/层压截面 → 边缘清漆 → 少量露浅木色 | 若网格确实表现分层，沿**板厚方向**做极细的浅深层线；不要把顶面木纹绕到边缘，也不要给整圈高对比白色破边。照片分辨率不足以判定层数或单层厚度。 |
| 钢管与靠背托片 | 暗色钢基底 → 旧浅象牙色漆膜 → 局部漆膜缺口 → 少量氧化/污垢 | 完整漆膜 Metallic=0，Roughness **0.32–0.48**；仅缺口中露出的干净钢 Metallic=1，Roughness 可从 **0.3–0.55** 试起；锈和污垢仍为非金属，通常更粗糙。掉漆主要在靠背上横管、受握持的转角、下横撑、管件接触/焊点附近，大片直管应保持安静的连续反光。勿把整条钢管设成金属。 |
| 固定点和托片 | 黑/暗色螺钉头、银灰托片分别遮罩；观察到露金属才设 Metallic=1 | 背面托片比木板偏冷；座面小黑固定点不能统一刷亮银。具体镀锌与否无法从照片确认，“镀锌”只是一种候选表面，不应写成来源事实。 |
| 脚帽 | 略黄于钢架的旧塑料样表面 → 微小接地擦痕/污迹 | Metallic=0，Roughness **0.55–0.75** 起步；近景保留柔和宽高光，脚底接地处局部更脏。旧椅实物材质成分未知。 |

上述范围依 [Adobe OpenPBR 材质说明](https://experienceleague.adobe.com/en/docs/substance-3d/general-knowledge/openpbr/openpbr-overview)给出的物理分类：木、塑料、油漆为电介质；裸钢为金属；金属度一般取 0/1，漆面应作为覆盖在金属上的独立层，清漆可由 Coat 表现。数值没有摄影测量依据，需要在**同一色彩管理与固定中性灯光**中同时检验高光形状、亮度及色相，再回到镜头光照复核。粗糙度细节的分布比全局“更亮/更暗”更能区分清漆木板和粉末涂层。[Adobe Designer 材质面板](https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/workspace/3d-view/material-properties)也支持按物理尺寸、UV 轴向和独立 Coat 粗糙度校验纹理比例。

## Painter / Designer → Blender 的具体做法

1. **先按真实材质分件与定向 UV。** 座板正反面、背板、侧边、管架、托片、螺钉、脚帽各有明确区域；至少座板与背板分别控制纹理方向和尺度。Painter 的[几何遮罩](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/interface/layer-stack/geometry-mask)能按网格名或 UV Tile 限定层；[Fill 投影](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/painting/fill-projections/fill-projections)支持 UV、平面、三平面等方式。木纹以板材方向为准，三平面只作为复杂部位的补救，避免每个面重复同一段花纹。
2. **木材先做可读的中、大尺度，再加微细节。** Designer 构建两套相关但不完全相同的板面纹路：座面有宽幅弯曲纹、背板以较细长纹为主；BaseColor、Roughness、微 Height/Normal 分开输出。把清漆的反射变化放在 Roughness/Coat，不把阴影、AO、划痕全部烘进 BaseColor。现有项目 `school_board.sbs` 用 [Poly Haven plywood](https://polyhaven.com/a/plywood) 作输入，其[许可为 CC0](https://polyhaven.com/license)，可以作为合法的原料继续调整；但这套源贴图的规则细纹与实物座面宽幅弯曲纹并不完全相同，不能直接平铺即视为完成。来源、物理周期、法线方向和哈希已在 [`manifest.json`](../../02_assets/textures/generated/wood_groups/manifest.json)登记。
3. **钢架用遮罩而不是通体“旧化”预设。** 底层钢、象牙色漆、缺口、氧化、灰尘分层。先烘焙 Position、Curvature、AO、World Space Normal；Adobe 的 [Metal Edge Wear](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear)依赖这些图并输出灰度遮罩。将它作为初始候选，手动删掉直管上不符合照片的均匀磨损，再在受撞部位少量补画。若木/钢共用一个 Texture Set，用网格遮罩或 ID 保证钢磨损不会串到木板。[Painter 烘焙说明](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/baking/how-to-bake-mesh-maps)区分输入高模与“低模当高模”：只有独立高模 → 低模的投射，才可声称完成高低模细节烘焙。
4. **确认分辨率来自实效像素密度。** 当前单张 2K 图集分给 26 个部件，木板区域占比和 UV 拉伸可能先限制精度。先量座/背板 UV 像素密度与近景实际像素，再决定改成独立 4K 木板 Texture Set、钢架 2K/4K，或 4K 工作母版按镜头需要下采样；提高导出尺寸本身不能修复低纹理密度、重复花纹与几何错误。Painter 支持逐 Texture Set [不同导出分辨率](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export-window/export-settings)。UV 岛需要充足 padding，避免 mip 级别串色；见 [Adobe padding 说明](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/technical-support/workflow-issues/export-issues/texture-dilation-or-padding)。
5. **输出与验证。** 从 Painter 输出 BaseColor、Metallic、Roughness、Normal OpenGL，AO 单列；如 Height 只是微细节，先让它合入最终法线，不默认驱动 Blender 位移。Adobe [输出模板](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export-window/output-templates)可生成含烘焙与绘制细节的 Normal OpenGL。Adobe [Painter 项目配置](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/interface/project-configuration)明确 Blender 推荐 OpenGL，Unreal 推荐 DirectX；换向必须重烘或正确翻转绿色通道，不能只改文件名。在 Blender 把 BaseColor 按颜色读取，Roughness/Metallic/Normal/AO 按数据（Non-Color）读取，法线经 Normal Map 节点连接。固定最终三角化/法线后再烘高低模；Blender [Cycles 烘焙文档](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)说明切线空间 normal、Selected to Active、射线距离与 cage 的用途。

## 需要验收的画面

- 中性环境下，座面在大约 0.4 m 宽的真实尺寸中能读出连续木纹；背板纹理更平静，板侧纹理与截面正确。清漆随转角产生连贯高光，细划痕只在高光中显现。
- 管架正视、侧视与靠背近景：大面积象牙漆膜完整，缺口与锈集中且尺寸多样；金属度贴图在完整漆面为黑、露钢点为白，脚帽和木板也为黑。AO 不用于把各材质 BaseColor 变脏。
- 在 Painter 与 Blender 相同中性环境和项目主镜头各检查一次 100%、50% 尺寸；确认木板 UV 无明显接缝、法线 Y 方向正确、mip 下无串色，再决定交付。当前研究不能替代实际贴图和渲染验收。
