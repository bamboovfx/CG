# 扫描辅助木材表现层

本目录是用户否定低细节表现层后的新配方。工艺层继续引用 `tripo_wood_reference` 的现有贴图，原文件保持；表现层采用Poly Haven `wood_table_worn` 原生8K的CC0 Diffuse、Rough、Displacement，位置／长划痕另在4K直接采样。

每块板的 `.sbs` 与 `.sbsar` 导出12份 `Raw_*` 色图／蒙版／高度及BaseColor、Roughness、Normal、Metallic、AO、EffectHeight。源色图为JPEG、高度为PNG，输出16位PNG不代表源颜色成为16位无损扫描。实际来源与许可在 `02_assets/textures/external/polyhaven_wood_detail/manifest.json`。

配方初始Scratches／Age／Wear默认值0.85／0.70／0.80；最终Blender与五通道导出使用0.95／1.0／0.95。`07_pipeline/scripts/validate_wood_detail_sd.py` 以明确参数重渲SBSAR，验证表现归零和工艺保护。Blender读取未乘强度的 `Raw_*`，避免双重乘权重。

生成器为 `07_pipeline/scripts/tripo_wood_detail_sd.py`。当前候选、100%裁片、实物尺度特写与限制见 `06_review/tripo_wood_detail_20260930/report.md`。视觉待评审，不能仅凭源8K、输出4K或技术检查宣称达标。
