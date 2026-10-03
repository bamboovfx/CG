# 课桌旧漆钢材 · Substance Designer

## 2026-09-27文件清理说明

固定 `.sbs`、`.sbsar`、资源图片、导出贴图与当前材质评审工程均保留。课桌现归入 `../../work/classroom_props.blend`，通过 `../../library/classroom_assets.blend` 发布。下文是历次制作记录；其中提到的旧独立 `school_desk.blend`、`07_pipeline/cache/desk_*` 回退副本及一次性探测、接入、提交脚本已停用或清理，不再作为操作入口。后续直接编辑当前材质源；保留工具见 [脚本入口](../../../07_pipeline/scripts/README.md)，重建前核对其输入与现有源。

## 当前修正：三维锈蚀与真实置换（2026-09-11）

固定工程 `../../work/school_desk.blend` 已修正旧 UV 锈边拉长、像素方块和仅有凹凸的问题。下面原有章节保留上一轮 SD 制作记录；其中“旧 UV 遮罩控制斑块”“仅 Height 凹凸”和倒角法线检测的描述，已被本节的 Blender 资产实现取代。SD 的 `.sbs`、`.sbsar` 和原始分层图片此次未改动。

- `NG_Desk_Corrosion3D`：锈蚀边界采用资产局部米制三维噪声，主斑块频率 65/m，另有 620/m 边界细节与不规则孔蚀。旧 2K Wear/Rust 图片保留但断开，印字仍使用原 UV。斑块位置随新场重新分布；脚底、弯管外侧和桌肚切边的空间定位继续保留。
- `NG_Desk_LocatedWear_DisplacementSafe`：沿用脚底、弯管和桌肚边缘定位，移除活动链路中的倒角射线依赖，使同一套遮罩能用于真实置换。它不会自动识别未来新增的任意几何边缘；模型尺寸改变后应重新检查定位范围。
- `NG_Desk_CorrosionRelief`：独立控制漆膜厚度、腐蚀深度、翘边、氧化颗粒与 SD 4K 微表面。普通金属腐蚀深度参数为 0.24 mm，底杆为 0.38 mm；这是孔蚀项的上限，实际深度由噪声和锈遮罩调制，完整高度还包含基底凹陷、漆层和微表面。
- 六类金属材质设为 `Displacement and Bump`，真实高度连接材质输出。`NG_Desk_PaintedSteel_DisplacedSurface` 保留原调色/粗糙度控制，断开旧重复 Bump。不要再叠加同一张 Normal。
- 金属对象新增可关闭的 Simple 细分修改器，基础网格、UV、相机和灯光未改变。大于 500 面的金属对象开启 Cycles 自适应细分，目标 2 px、最多 8 级、画外倍率 64；小五金使用固定渲染细分 2 级。普通实体视图不显示着色器真实置换，评审使用 Cycles。

| 节点组 / 控制 | 当前值 | 作用 |
|---|---:|---|
| Corrosion3D / Wear Threshold | 桌腿 0.590，底杆 0.365，五金 0.575，桌肚 0.625 | 数值越低掉漆越多 |
| CorrosionRelief / Paint Thickness m | 0.00009 | 漆膜厚度 0.09 mm |
| CorrosionRelief / Corrosion Depth m | 0.00024 / 底杆 0.00038 | 不规则孔蚀最大系数 |
| CorrosionRelief / Chip Rim m | 0.000045 | 掉漆边缘微翘 0.045 mm |
| CorrosionRelief / Microheight m | 0.00035 | 原 SD 分层微表面高度范围 |

验证：已检查相同灯光、相同机位的全景、弯管、底部和底杆微距，1500 px 近景、192 spp、不使用降噪。透明轮廓 A/B 在相同相机、网格和细分条件下切换 BOTH/BUMP，有 4990 个像素的 alpha 差值超过 0.1，证实存在真实几何轮廓变化。重新打开固定工程后，原网格/UV 指纹、相机灯光一致，63 个图片依赖全部有效且路径相对化。资产仍待用户视觉验收，未写入整景或资产库。

评审：`../../../06_review/desk_corrosion/review.md`；验证：同目录 `validation.json`。可直接打开的修改前副本：`../../../07_pipeline/cache/desk_corrosion/before_corrosion.blend`，已重映射相对贴图路径。重建/评审/验证/提交脚本分别为 `refine_desk_corrosion.py`、`render_desk_corrosion.py`、`verify_desk_displacement.py` 和 `commit_desk_corrosion.py`。首次接入和提交脚本有防重复保护，后续应直接调整现有节点。

---

更新：2026-09-10。原生可编辑程序化材质，91 个节点、16 个公开输入；无照片贴图、无扩散模型生成图。

本轮已增加独立浅干裂、可调掉漆翘边，并把材质接入固定课桌工程 `../../work/school_desk.blend`。模型、UV 和原有正面标记保留；资产仍待用户视觉验收，未替换进整景。

- 源工程：`school_desk_painted_steel.sbs`
- 可复用材质：`school_desk_painted_steel.sbsar`
- 独立灯光评审：`desk_material_lookdev.blend`
- 贴图：`../../textures/generated/school_desk_sd/{frame,brace}/{2k,4k}/`
- 来源、参数、哈希及验证：贴图目录中的 `manifest.json`
- 评审图：项目根目录 `06_review/sd_material/`
- 课桌同机位前后对照：项目根目录 `06_review/desk_crack_wear/{before,after}_{upper,foot,full}.png`
- 模型与路径验证：项目根目录 `06_review/desk_crack_wear/validation.json`

## 干裂与边缘磨损控制

在 SD 中打开 `.sbs` 后，选择图本身，可在 `04 Paint cracking` 与 `05 Edge wear` 参数组调节：

| 参数 | 默认值 | 用途 |
|---|---:|---|
| CrackAmount | 0.46 | 局部裂纹覆盖与强度；0 完全关闭 |
| CrackScale | 22 | 20 cm 纹理内的细胞尺度；越大，裂片越小 |
| CrackWidth | 0.018 | 相对细胞的裂缝宽度；尺度变化也会改变毫米宽度 |
| CrackDepth | 0.065 | 裂缝凹陷占总 HeightRange 的比例 |
| ChipRimHeight | 0.14 | 随机掉漆斑块的漆膜翘边高度 |
| EdgeWearAmount | 1 | 对 ExtraWear 外部定位遮罩的强度控制 |

裂纹由扭曲 Voronoi 边界、局部老化噪声和完整漆面遮罩相乘得到。浅裂纹影响 Height、Roughness 和少量 BaseColor，不增加 Metallic，也不把每条裂纹都变成裸钢。CrackAmount 与控制氧化的 Age 独立。默认深度是 `0.065 × 0.6 mm × 裂纹遮罩`，在本轮 0.46 强度下最深约 0.018 mm。

模型使用 `NG_Desk_GeometryWear`，各金属材质中节点标签为 `EDGE WEAR / width / fresh steel`：

| Blender 控制 | 默认值 | 用途 |
|---|---:|---|
| Edge Wear Amount | 0.85 | 模型定位磨损强度；0 退回原来的 UV 掉漆范围 |
| Edge Width m | 0.0016 | 边沿检测及桌肚窄边范围，以米为单位 |
| Edge Oxidation | 0.28 | 新磨损中氧化比例；底杆为 0.50，降低会露出更多钢 |

模型磨损采用 Cycles 倒角法线与表面法线的差值，叠加毫米级噪声打断连续边线；脚底、弯管外侧及桌肚前后切边另加按当前模型尺寸定位的范围。圆管的大面积连续曲面不会仅因弯曲就全部掉漆。旧 UV 遮罩仍控制原有斑块，边界阈值收紧以减轻插值发糊。细观漆、钢、锈采用原生分层贴图，按 **20 cm** 三向投影映射。

模型定位磨损是 **Cycles 着色节点**，不是烘焙曲率，不能声称已经包含在可平铺 SBSAR 中。切换 Eevee 或移植到 UE/Houdini 时，需要另行烘焙或实现对应逻辑。`ExtraWear` 仍是 SD 接收资产定位图的接口，本轮模型定位在 Blender 内完成。`desk_material_coordinate_origin` 提供资产局部米制坐标；移动整张课桌时应一起移动此 Empty。桌肚定位数值与当前尺寸绑定，几何尺寸修改后要重新检查。

分层输出在 `../../textures/generated/school_desk_sd/layers/{2k,4k}/`，含 Paint/Steel/Rust 各自的 BaseColor、Roughness、Height。Blender 使用 Height 生成物理尺度凹凸，未重复叠加同一 Normal。资产分层组合保留漆层落差；`ChipRimHeight` 是 SD 平铺合成输出的翘边控制，不控制 Blender 新生成的资产边缘。

## 本次清晰度修正

原 4K 输出的 Height/Normal 在微距中仍显软：最终 Height 的整体 Blur HQ 过滤了微表面，过强 Warp 又在掉漆边界制造密集的露钢碎点。修正时移除了末端整体模糊，将 Warp 从 0.0025 降到 0.00018，并将露钢和翘边遮罩的模糊半径收窄。新增了独立漆面微粗糙度、浅划痕与更清楚的氧化孔蚀。

所有原子和实例节点显式继承父图分辨率。源图默认父级设为 4096×4096，导出时明确指定 2048 或 4096。色彩、标量和法线交付为 16-bit PNG；法线保留 OpenGL 约定。

当前使用 CLI 编译和导出，未控制正在运行的 SD GUI。若 SD 已打开旧图，需要在保存用户改动后重新载入磁盘文件；当前内存中的图和 3D 预览并未由本次 CLI 刷新。若改用 SBSAR，导入端也须设定其输出分辨率为 4096。本机实测：sbsrender 未传入输出尺寸时，此 SBSAR 计算为 256×256；传入 `$outputsize@12,12` 后才是 4096×4096。放大 256/512 的预览不能验证此 4K 交付。源 SBS 的默认父级预览设置不等于 SBSAR 在所有宿主中的默认尺寸。

## 使用尺度和参数

一张平铺纹理对应 **20×20 cm**。4K 像素间距约 **0.049 mm**。Height 的 0–1 对应 **0.6 mm** 总范围；实际漆层落差约 0.1 mm。Normal 已按此尺度计算，不应再次叠加同一 Height 的全强度凹凸。

| 预设 | Wear | Age | DirtAmount | ChipScale | 用途 |
|---|---:|---:|---:|---:|---|
| frame | 0.36 | 0.60 | 0.14 | 3 | 桌腿、托盘的完整漆面为主 |
| brace | 0.56 | 0.75 | 0.20 | 3 | 底部横杆的重锈蚀 |

其余暴露参数：PaintColor、RustColor、PaintRoughness、SurfaceSize（cm）、HeightRange（cm）。ExtraWear 是可选灰度输入：白色增加掉漆，可连接手绘定位或已选取边缘的曲率遮罩。不要把未经处理的完整曲率图直接当成所有表面的磨损程度。frame / brace 的 CrackAmount 分别为 0.46 / 0.52。

BaseColor 使用 sRGB。Roughness、Metallic、Normal、Height、AO、WearMask、RustMask、PaintMask、DirtMask 使用 Non-Color。AO 不乘入 BaseColor。只有裸钢为金属，漆与氧化物为非金属。

当前默认种子为 3087，由源图控制。随机程序化分布适用于材质族；模型端已接入本节所述定位磨损。固定课桌工程更新了六类金属材质，原材质节点与原贴图保留；几何和 UV 指纹一致。

## 验证与参考边界

通过 Adobe sbscooker 原生编译；两组预设均导出 2K/4K。脚本检查漆/锈/钢遮罩分区、锈不越过掉漆范围、氧化物粗糙度、平铺边界差分，并验证只改 Age 时 WearMask 不变。具体数值在 manifest.json。

本轮另验证 CrackAmount=0 时 CrackMask 为零、裂纹不越过完整漆面、深度控制改变高度但不实质改变掉漆。D3D11 在部分阈值像素有微小计算差异：深度对比 WearMask 平均误差约 6.7e-9，最大约 0.00142；没有把此 GPU 数值差异误标为逐位完全一致。脚本快照、暂存源和检查数据保存在 `07_pipeline/cache/desk_cracks/`。4K 遮罩分区最大误差约 1.2e-7。

Cycles/OptiX 独立评审采用固定软箱灯、1440×1440、192 spp，无景深和降噪。`*_macro_60mm.png` 显示约 6 cm 视野；`*_after_1to1.png` 是原图像素直接裁切的通道检查。上述检查证明本轮细节输出可用，不等于已完成课桌最终实物匹配。

方法参考：[Andrea Riccardi — Painted Metal Material](https://andreariccardi.artstation.com/projects/QzmB2B)。直接 HTTP 访问曾返回 403，随后通过已连接的 Chrome 成功查看作品页，以及 Age 0.625 / Worn 0.4 的 1920×960 参考图。未复制其贴图或节点工程。

视觉对照：参考图的漆膜断口有明确厚度、裸钢反光与氧化颗粒分开，漆面存在细裂纹。当前课桌材质采用灰米色旧漆、桌腿低掉漆和底杆重锈两组预设，颜色与磨损程度按 `props_01` 实物参考取舍。本轮已经接入浅裂纹、脚底、弯管和桌肚边缘磨损；旧 UV 磨损图在极近距离仍会受到原始分辨率限制，不能宣称完成实物扫描级匹配。

## 重建入口

项目 `07_pipeline/scripts/`：

1. 已保存的 `.sbs` 是当前权威源。`build_desk_substance.py` 是早期基础图生成器，单独运行会移除后续分支；勿覆盖手工调整。
2. `add_desk_cracks.py` 从本轮保留的 `before_cracks.sbs` 增补分支，输出 cache 暂存源；不会直接覆盖固定 SBS。
3. Adobe `sbscooker.exe` 编译后，验证暂存图，再更新固定源；`export_desk_substance.py` 导出两种预设、分层贴图和验证/哈希。
4. `render_desk_sd_lookdev.py` 重新生成独立材质评审；`render_desk_crack_review.py` 渲染课桌同机位对照。
5. `apply_desk_crack_wear.py` 是首次接入脚本，对已接入工程会拒绝重复应用。后续直接编辑固定工程中现有的材质节点。
6. `commit_desk_crack_wear.py` 只在已检查暂存渲染后使用，核对源文件哈希，验证几何/UV 和相对路径，再写入固定工程。

本轮修改前的课桌回退副本为 `07_pipeline/cache/desk_cracks/before_crack_wear.blend`。其图片路径保持原工作目录的相对写法，需放回原工作路径使用，或恢复时显式重映射；不要直接在 cache 中打开后把相对图片缺失当成源资产损坏。
