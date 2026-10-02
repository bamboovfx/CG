# 喇叭旧塑料材质 · 2026-09-16

已在 SD 原生节点图中制作，并将 4K PBR 绑定至 `classroom_equipment.blend` 的 `AST_wall_speaker` 外壳和格栅，独立材质为 `Speaker / SD worn plastic`。保持原有暖灰色和模型结构。

- 源工程：`02_assets/materials/speaker_plastic/speaker_plastic.sbs`，48 个原生节点。
- 编译材质：同目录 `speaker_plastic.sbsar`。
- 贴图和来源记录：`02_assets/textures/generated/speaker_plastic/manifest.json`。
- 可调参数：PlasticColor、BaseRoughness、PolishAmount、ScuffAmount、ScratchAmount、AgeAmount、ReliefDepth、TileSize；ExtraWear 是可选的局部磨损输入。
- 通道：BaseColor、Roughness、Normal、Height、Metallic，以及 PolishMask、ScuffMask、ScratchMask。
- 映射：现有米制 UV × 4，25 cm 一次平铺；OpenGL Normal，Metallic 恒为 0。
- 已检查：Adobe cooker/render 成功；八张 4096×4096 输出；Blender 四个 PBR 通道路径、颜色空间及尺寸；同灯光前后对照和近景。

视觉参考：[Plastic Worn](https://substance3d.adobe.com/community-assets/assets/eb6b672e0665fbdefa374e4ddd97e7c45037ff97)，作者 Malte Resenberger-Loosmann。网页原件为 Painter SPSM，只借鉴表面层次，没有使用或重新分发第三方材质文件。

`before.png`、`after.png` 使用相同灯光；`detail.png` 展示浅划痕和光泽斑驳。当前版本是轻至中等使用磨损；未烘焙模型曲率或 AO，因此 ExtraWear 默认为空，不声称已有沿模型边缘定向的磨损。用户视觉验收待定，未更新整景或资产库。

源图通过 Adobe 命令行编译验证。SD 窗口文件对话框的自动控制未能可靠定位输入字段，尚未完成 GUI 内编辑检查。
