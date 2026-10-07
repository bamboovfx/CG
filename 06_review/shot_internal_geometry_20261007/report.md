# 镜头内部模型恢复验收

2026-10-07。技术通过并原位发布；镜头艺术验收沿用原状态。

用户要求模型留在内部。读取当前e786ccef保存源，在候选将11033个网格恢复为本地可编辑数据；发布文件66,310,940字节（63.24MiB），SHA256 `450e8122ef6d26a1980d5443e4d7a74a7269486851f47094485811d9fc58f270`。主入口仍为 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。

313个原材质、46个节点组、15,115对象、有效材质绑定、实例共享关系、几何UV及全部属性、相机世界与动画的保护快照无变化。保留OBJECT材质槽，模型和shading都在镜头内修改。所有网格、材质和节点组本地可编辑，外部blend库0。实际顶点及黑板／课桌／课椅shader参数改值后恢复，通过独立重开验证。

84张此前外置的打包图片仍为相对路径，逐张文件哈希一致；全图像路径和解释设置保持。当前413项依赖清单包含镜头及贴图，排除旧几何库；既有Abrasion、5张opdef人物图及Arial Narrow缺失保持。库文件保留为历史资料，不再是当前几何编辑入口。

同帧临时Cycles CPU／640×270／32spp对照，平均8bit差异0.010855/255，大于32的像素占比0.012153%；门槛为均值≤0.5且该占比≤0.5%。正式渲染设置未改，构图、摆位和光照另作人工画面核对；此项不代表镜头艺术通过。

原e786ccef文件保留于忽略缓存 `07_pipeline/cache/shot_internal_geometry_20261007/source_before.blend`；发布前后源哈希检查避免覆盖新保存，未操作其他Blender窗口和独立Designer测试。

证据：[候选重开](candidate_verification.json)、[正式重开](published_verification.json)、[同帧比较](pixel_comparison.json)、[当前依赖](upload_manifest.json)。

Git同步结果待提交后追加。

413 dependencies independently checked with SHA256: 0 errors. Task card validation passed. Global PM regeneration remains blocked by 77 existing historical evidence errors; unrelated missing files were not restored.
