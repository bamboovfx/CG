# 钟表黑漆 imperfection · 2026-09-14

已用原生 Substance Designer 节点制作 4K、16-bit 粗糙度，替换钟表黑漆原来的满铺斑驳。基于当前未保存源工程制作与接回，模型顶点、位置、原 UV 和划痕 Bump 设置保留。新增 `ImperfectionMeters` UV 只用于新的粗糙度。

## 参考与判断

- [Zak Boxall — Making realistic materials in Substance](https://zakboxall.artstation.com/blog/N0dE/making-realistic-materials-in-substance-steel-free-sample-textures)：已查看 imperfection 图板，并阅读分层制作过程。主要参考局部擦拭方向、干净区域与多尺度划痕，未使用作者图片作为贴图。
- [Adobe — MDL Malachite Material Breakdown](https://www.adobe.com/learn/substance-3d-designer/web/mdl-malachite-material-breakdown)：参考其独立处理 smudge / fingerprint 粗糙度遮罩的流程，不采用石材本体外观。
- 当前问题：旧 `closeup_polymer/Roughness.png` 直接输入 Roughness。后盖归一化 UV 与侧壳米制 UV 共用 4 倍平铺，也造成尺度不一致。

## 文件与调节

- 原生工程：`02_assets/materials/clock_imperfection/clock_imperfection.sbs`
- 发布包：同目录 `clock_imperfection.sbsar`
- 贴图：`02_assets/textures/generated/clock_imperfection/`
- `BaseRoughness = 0.37`：干净漆面的基础反射宽度。
- `WipeAmount = 0.65`：提高局部擦拭处的粗糙度，控制擦拭痕强弱。
- `OilAmount = 0.55`：降低局部油膜处的粗糙度，控制更清晰的局部反射。
- 40 cm 平铺；实际输出 Roughness 约 0.326–0.418，平均 0.370。
- Blender 保留原 Height → Bump；原 ScratchMask 以 0.025 幅度加到新的 Roughness。Base Color、Metallic、涂层参数保持用户原值。
- 新增节点保留默认名称；阶段说明位于注释框中。原生图可在 SD 打开继续编辑，使用本机 Adobe cooker / sbsrender 实际编译输出。

## 验证与恢复

评审图在 `04_renders/sq010/sh010/clock_imperfection/v001/`：`before_back.png` 与 `after_back.png` 灯光、机位、曝光、随机种子相同；`after_front.png` 检查完整表面和侧壳。已检查反射连续性，满铺颗粒斑驳明显减弱，局部擦拭和原有细划痕仍可见。

材质备份 `Clock / Before imperfection`；当前源工程的接回前快照 `07_pipeline/cache/clock_imperfection/live_before_apply.blend`。资产库只更新对应材质和新 UV，不替换任何几何。镜头 MCP 保持断开；打开中的镜头需重新载入资产库才显示新材质。

这是材质制作与近景检查结果，最终强度仍以你的场景光照和审美验收为准。
