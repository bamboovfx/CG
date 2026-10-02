# 胶脚工艺层与表现层 — 2026-10-01

本轮按前轮分出的四个底部脚套制作，已应用到 `07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend`。参考原课椅照片中的浅黄旧胶质，采用轻度旧化。

工艺层为浅黄模塑胶质、哑光反射和微起伏，Metallic=0；表现层为温和黄化、浅擦伤、稀疏细划痕及近地灰污。四件根材质独立，Age／Wear／Scratches／Dirt可分别调整，共享原生SD内容。底边定位与三向投射锁在本胶脚；原有几何、两套UV、法线、其它材质及场景变换保留。

原生SD65节点、18张4K输出；实际使用9张打包图。SD四表现参数归零后，六个最终通道与工艺通道像素差0；Blender实际固定种子归零渲染与直接工艺渲染最大差1个8位值。独立重开55项通过，确认四件独立材质、实际通道接线、本地绑定和9张4K图像打包／色彩空间。工艺恢复、技术检查通过；艺术效果待用户视觉确认。

整体效果与近景均使用原三点布光、透视相机。OptiX预览遇到CUDA非法地址错误，本轮改用CUDA完成渲染；没有改写正式文件的原渲染设备设置。候选制作前保存实时未保存编辑；写入时Blender已关闭，因此使用用户随后保存的最新磁盘工程为基础，并另存 `07_pipeline/cache/chair_foot_cap_materials_20261001/pre_apply_live.blend` 后只追加四个材质。

![四个胶脚](feet.png)

![近景](front_cap.png)

证据：`candidate.json`、`applied.json`、`sd_zero_validation.json`、`blender_zero_validation.json`、`reopen_validation.json`。材质说明见 `02_assets/materials/chair_foot_caps/README.md`；可编辑SD源与SBSAR同目录。
