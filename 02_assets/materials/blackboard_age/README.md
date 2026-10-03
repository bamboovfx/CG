# Blackboard / Aged baked green coating

材质是钢板烤漆书写面的制作假设，尺寸 4.143805 × 1.49 m。保留现有木框与几何。

`school_blackboard_baked_coating.sbs` 是原生 Substance Designer 源，`.sbsar` 为对应编译结果。`inputs` 的 8 张 4K 遮罩根据使用行为生成，固定种子 190926。另有 `CC0EraserDetail` 图片输入，路径和授权见 `../../textures/generated/blackboard_age/manifest.json`。

图的图片输入需要绑定 manifest 内记录的对应文件；重建脚本 `07_pipeline/scripts/blackboard_age_substance.py` 自动绑定输入、编译并导出，完整命令也已记录在 manifest。单独打开 SBS 时，若尚未绑定图输入，请先绑定这些图片再预览。

| Substance 参数 | 当前值 | 用途 |
|---|---:|---|
| SunFadeAmount | 0.38 | 宽泛的靠窗侧褪色，非即时光斑 |
| EmbeddedChalkAmount | 0.11 | 长期嵌入灰与轻微白化 |
| RecentWipeAmount | 0.10 | 最近板擦路径的覆盖 |
| ChalkDetailAmount | 0.38 | 颗粒和板擦纤维细线 |
| PolishAmount | 0.82 | 擦拭磨平对粗糙度的影响 |
| GhostAmount | 0.08 | 不可辨读的断笔残留 |

Blender 中独立材质名为 `Blackboard / Aged baked green coating`。BaseColor 使用 sRGB，Roughness / Normal / Abrasion 使用 Non-Color。物体坐标映射保留现有 UV；Noise 的米制尺度补充约 0.33 mm 的涂层微齿，磨损遮罩降低其强度。Bump Distance 25 μm 是着色范围设定，不是表面实测值。

输出为艺术制作的 PBR 通道；照片只参与残留遮罩，粗糙度与微法线并非实物扫描测量。不要将单一灰度纹理同时解释为真实高度、粗糙度和金属度。涂层 Metallic 为 0。
