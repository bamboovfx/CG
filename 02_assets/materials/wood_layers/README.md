# 木椅分层材质

编辑源：`school_wood_layers.sbs`。原生SD归档：`school_wood_layers.sbsar`，包含4K CC0木纹资源。源文件中位图路径对应本工程现有Poly Haven plywood；移动工程时需重定位该资源，归档已包含位图。

## 工艺层与表现层

工艺层包含自然木纹、琥珀着色、打磨涂层及轻微木纤维起伏。`Process_*` 为独立五通道。木材Metallic为0，表面AO白色；实际椅子结构遮挡由Blender光照计算，没有将AO乘入基础色。

表现层参数：`Scratches=0.38`、`Age=0.30`、`Wear=0.42`。三个参数归零后最终五通道与工艺层一致。`FinishRoughness=0.34` 控制基础粗糙度；`SurfaceSize=60` 为cm；`HeightRange=0.012` 为cm，即总高度范围0.12mm。

最终 `BaseColor/Roughness/Metallic/Normal/AO` 已设置PBR语义，可用于Substance材质导入。另输出 `ScratchMask`、`LongScratchMask`、`AgeMask`、`WearBreakup`，供资产定位与逐层调节。输出纹理位于 `../../textures/generated/wood_layers`，2048×2048；原生4K位图进入配方，在2K输出前处理。

## Blender 验证工程

`../../../07_pipeline/cache/wood_layers_20260930/wood_layers_studio.blend` 使用当前教室工程的木椅，在独立场景中制作两组材质：

- `Wood / 工艺层 / 木纹着色与涂层`：读取SD工艺五通道与高度。
- `Wood / 表现层 / 划痕老化磨损`：三个独立强度；长划痕、浅划痕、老化与磨损分别影响颜色、粗糙度和法线。

选中座面或靠背，进入Shader Editor，在引用表现层组的Group节点中调整 `Scratches/Age/Wear`。节点保留默认名称，说明放在注释框。材质分别单独创建，调整座面不会自动覆盖靠背。

木纹以 `WoodGrainMeters` UV映射，周期0.6m；法线使用同一UV。边缘磨损由 `SurfaceMeters` 与 `surface_span_u/v` 限定在18mm带内，再由SD破碎蒙版打断。SD最终五通道本身是可平铺表面示例，不等于含该资产边缘分布的UV图集；Blender候选中的表现层才包含资产级定位。

保存工程为1200×1200、Cycles 64 samples、AgX Medium High Contrast、曝光0、透视52mm相机、三盏面积灯。评审目录中有工艺层、加划痕、加老化、加磨损四张同光全景，以及座面和掠射光近景。当前教室工作工程未覆盖。

## 来源与复现

- 原始木纤维：[Poly Haven plywood](https://polyhaven.com/a/plywood)，CC0；既有工程素材。
- 用户木椅照片：只作视觉参考，未进入可分发贴图。
- `07_pipeline/scripts/wood_layers_sd.py`：原生节点与资源构造、烹制和渲染。
- `07_pipeline/scripts/wood_layers_blender.py`：木椅独立验证场景与分层渲染。
- `07_pipeline/scripts/verify_wood_layers.py`：保存后读回验证。
- 贴图哈希、尺度、参数与调用命令：`../../textures/generated/wood_layers/manifest.json`。
