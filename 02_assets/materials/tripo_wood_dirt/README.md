# 独立表面脏渍层

按2026-09-30用户新增参考制作：保留上一版已经改善的老化与磨损，另加细小深色点、灰褐附着残留和淡擦抹痕。

原生Designer源为 `wood_surface_dirt_seat.sbs`、`wood_surface_dirt_back.sbs`，归档为同名SBSAR。输入是直接4096采样的技术位置蒙版和已有CC0扫描颜色／粗糙度，位置与细碎内容分开。参考照片只用于观察，不采样或拼贴其像素。

扫描来自 [Poly Haven wood_table_worn](https://polyhaven.com/a/wood_table_worn)，源文件及许可／哈希沿用 `02_assets/textures/external/polyhaven_wood_detail/manifest.json`。本次没有重新下载素材。

输出位于 `02_assets/textures/generated/tripo_wood_dirt/{seat,back}`，均为4096²、16位PNG。`DirtColor` 用sRGB；`DirtMask`、`DirtRoughness`、`DirtHeight` 用Non-Color。另外导出 `ResidueMask`、`SmudgeMask` 供观察与继续制作。

Blender中在旧表现组之后串接 `Wood / 表面脏渍 / seat` 与 `back`。节点仍保留默认名称，材质内脏渍组默认名为 `Group.002`；控制 `Dirt` 独立于 `Age`、`Wear`、`Scratches`。`Dirt=0` 恢复最新输入版本，`Dirt=1` 为本次候选。颜色、粗糙度、基础／清漆法线和清漆响应一起变化，Metallic保持已有木材路径。

脏点半径约0.12–0.40mm，一般残留半径0.30–1.15mm，少数更大的残留约1.5–3mm长。擦抹包络半径7–11mm，但对比很淡。它们是不均匀、分簇的制作设定，不是对参考照片逐点复刻。

高度为少量表面附着物，Blender Bump Distance=25µm，实际高度乘图值与Dirt控制；细点约6µm比例。没有改动几何、轮廓或原UV，没有新增AO压暗；表面微凸起不应表现为裸木大坑。

复现入口：`07_pipeline/scripts/tripo_wood_dirt_sd.py`、`tripo_wood_dirt_blender.py`。后者只读取最新已保存的 `tripo_wood_detail.blend`，生成独立 `tripo_wood_dirt.blend`，不会替换教室主镜头。验证入口为 `validate_wood_dirt_blender.py` 与 `review_wood_dirt.py`。

这是独立脏渍通道和实时分层材质；没有把整套旧材质与新脏渍重新烘成一套最终五通道图。整套材质的视觉效果以Blender候选和同光渲染为准。

Blender在DirtColor之后乘线性色彩系数(0.38, 0.44, 0.52)，用于压深附着物反照率；保留原图的细碎色差。独立SD输出是未经该材质内校色的目标图，不代表完整叠加结果。
