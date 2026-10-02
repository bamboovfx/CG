# Tripo 课椅材质重制交付 · 2026-09-30

## 结论

已把当前 Tripo 椅子的材质重制为两组 4K UV PBR 贴图，并接回独立 Blender 文件。座板、靠背、漆钢管、裸露托片、螺钉和脚帽有分开的表面逻辑；已完成近景和整体 Cycles 渲染。**材质候选可供镜头测试，Tripo 原网格仍未达到正式次世代资产的几何验收标准。**

本次仅用 Tripo 椅子的未上色网格作为制材对象。外观判断来自 [AITA 实物椅照片](https://aita.ocnk.net/product/3087)及本地 `01_preproduction/references/props/20160220_201e63.JPG`、`20160220_47c158.JPG`、`props_01.jpg`；未用旧 Blender 椅模型或旧渲染决定颜色、木纹及磨损分布。照片只作观察依据，未投射或采样成资产贴图。原商品页也提醒照片有色差，因此颜色是中性灯光下的美术匹配，不是实测反射率。

## 材质制作

- 木板：项目已有 Substance Designer `school_board` 4K 图作为细木纹、微高度、粗糙度和清漆细划痕的原料；其底层素材来自 [Poly Haven CC0 plywood](https://polyhaven.com/a/plywood)，来源登记见 `02_assets/textures/generated/wood_groups/manifest.json`。在 Blender 中另做大尺度弯曲木纹和暖蜜色调；座板纹理比背板更明显，侧边用独立层压截面色。木材与清漆保持非金属，清漆由 Coat 控制。
- 钢架：以完整的旧象牙色漆为主体，靠背上管、接触处及横撑附近做稀疏掉漆、露钢和锈色；完整漆膜的金属度为 0，露钢局部为 1。灰色背板托片、暗色螺钉及偏黄哑光脚帽独立分件。
- UV：保留导入时原 UV，另建 `UV_Material`。木板和漆钢各用一张 4K 图集；木板 UV 面积占比从 0.154 提高到 0.763，等效方形边长约从 1609 px 到 3577 px。快速紧固件与脚帽使用参数材质，不挤占这两张图集。木板及钢架 UV 面内重叠检查各为 0 对。
- 输出：木板和漆钢各有 BaseColor、Roughness、Metallic、Normal OpenGL、AO 五张 4096² PNG；AO 独立存储，不乘入底色。最终网格三角化并保留 Tripo 导入的自定义法线，然后烘切线法线。Blender 中 BaseColor 用 sRGB，数据图用 Non-Color，贴图均打包。

这些层遵循 [Adobe OpenPBR](https://experienceleague.adobe.com/en/docs/substance-3d/general-knowledge/openpbr/openpbr-overview) 的非金属/金属区分和 [Blender Cycles 烘焙说明](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)的切线法线约定。进一步的实物观察、Painter/Designer 分层与验收方法见 [材质研究笔记](material_research_20260930.md)。

## 验证与边界

Blender 5.1.2 中读回最终 `.blend`：26 个网格部件均为三角面且有 `UV_Material`；10 张图均为 4096²、已打包、色彩空间正确，磁盘文件哈希与烘焙记录一致。UV 检查记录与最终读回见 `uv_validation.json`、`delivery_validation.json`。整体和近景 Cycles 渲染已完成。烘焙时曾发现座面亮斑，对照渲染确认由三角化丢失自定义法线造成；保留法线并重烘 Normal/AO 后，亮斑消失。

这次做的是**当前网格的材质和自身表面贴图**：没有独立雕刻高模与低模投射，也没有新建 Painter `.spp` 项目。Tripo 网格已有的管端、连接、边界/非流形问题及木板造型误差仍需建模修复；目前没有把候选并入正式教室镜头。材质照片中座板宽幅纹理、旧漆缺口只能作可信近似，不能宣称逐处复刻。

## 文件

| 用途 | 文件 |
| --- | --- |
| 最终 Blender 材质候选 | `07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_baked.blend` |
| 低模 FBX | `07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_low.fbx` |
| 两组 4K PBR 贴图 | `07_pipeline/cache/tripo_chair_material_v2_20260930/textures/` |
| 整体/近景渲染 | `07_pipeline/cache/tripo_chair_material_v2_20260930/baked_overview.png`、`baked_detail.png` |
| UV、烘焙、读回记录 | 同目录 `uv_repack_audit.json`、`uv_validation.json`、`bake_audit.json`、`delivery_validation.json` |
| 可复现脚本 | 同目录 `build_materials.py`、`prepare_bake_uv.py`、`apply_seat_figure.py`、`bake_pbr.py`、`verify_delivery.py` |

最终 `.blend` SHA256：`8b2f884cf79e381bb3c563684bb80f5595e0aa672ebc82f3a59f3225bb467a68`；FBX SHA256：`e0e0793439be347e4093bf488cc286f1a65e6e2b6d49fbbe89c8f29512cf6301`。
