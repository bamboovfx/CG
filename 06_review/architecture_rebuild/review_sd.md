# 建筑模块、Substance Designer 材质与连续窗帘 · 2026-09-11

最终源工程：`02_assets/work/classroom_architecture.blend`。8 个 AST 集合名、collection instance_offset 与门窗安装位置保持。`ARC_preview` 只用于评审，不应放入公共资产库。

## 本轮结果

- 门窗及轨道延续首版完成的独立框梃、双轨搭接、胶条、月牙锁、回弯拉手、锁芯、分段合页、C 型轨与支架；全部改用实际 SD 输出。
- 走廊低位窗带在门洞 `Y=2.7375..3.9625 m` 处断开。门合页在 +Y，把手在 -Y，室内面 -X，开口与朝向保持。
- 窗帘取消居中对称收腰，改为较低的侧向松束；束下自然散开，宽窄主褶合并和扭转；挂点之间浅弧下垂，挂点下方短挤褶在约 25 cm 内消退；束点附近三条 5–8 mm 的局部斜向张力褶，不给整块布加入噪声。自由边轻微卷转，静态姿态仅保留约 2 cm 的轻微抬起。
- 每块主体是**一块连续网格**：18,281 顶点、18,000 四边面。缝边和缝线使用同一网格的局部形变与 UV 材质，不拆成不会随模拟运动的布条。

## 实际查看的参考

原片 `drop_official_1080p.mp4` 的 154、160、168 秒图像是构图、色调、尺寸比例和安装方向的权威。五金截面、精确壁厚及动力学参数属于制作设定，不宣称原片测绘数据。

| 来源 | 已下载、已实际查看的图 | 用途 |
|---|---|---|
| [UR Community 窗户构件](https://www.ur-cm-support.jp/glossary/tabid135.html) | `reference_window.png` | 月牙锁、窗扇搭接、胶条、金属表面 |
| [TOSO C 型轨](https://item.rakuten.co.jp/auc-interia-kirameki/tocr-pa-cg-scrunner/) | `reference_track.jpg` | 金属轨、塑料滑块的独立材质与安装 |
| [SO LINEN 束带近景](https://so-linen.com/en/produkt/linen-curtain-tie-back-natural-linen/) | `reference_natural_tie.jpg` | 薄而有宽度的束带、经纬密度变化、自然泛旧色泽 |
| [MyStyleBox 亚麻近景](https://www.mystylebox.ca/pages/fabric-types-guide-and-mixing-textures) | `reference_linen_macro.jpg` | 平纹织造、粗细不等纱线和纤维杂色 |
| [Orné de Feuilles × fog linen work](https://www.ornedefeuilles.com/products/fog-orne-linen-curtain) | `reference_loose_drape.jpg` | 松弛悬垂、薄棉麻的逆光漫透射 |
| [Cerema 自然通风教室](https://www.cerema.fr/fr/actualites/prototype-outil-pilotage-accompagner-ouverture-nocturne) | `reference_classroom_breeze.jpg` | 微风下自由边与窗洞关系；最终幅度远小于参考中的风吹幅度 |

这些商业/机构照片只用于观察，不进入贴图，不标记为 CC0。LinenTailor 图片返回 404、Lilycolor 图下载 EOF，未列为成功检查素材。

## 实际 Substance Designer 交付

`02_assets/materials/architecture_rebuild` 包含 **5 套可编辑 SBS 与实际编译的 SBSAR**：

- `architecture_linen`：扫描纱线输入 → SD 原生调色 → 纱线微变 → 物理尺度 Height/Normal → Roughness / 漫透射分布。
- `architecture_enamel`：低对比漆面变化、微小橘皮、浅表细痕。
- `architecture_metal`：原生各向异性拉丝、粗糙度和微尺度法线。
- `architecture_glass`：极低对比微表面；门的隐私玻璃单独提高粗糙度。
- `architecture_polymer`：EPDM/聚合物细表面。

实际调用本机 Adobe `sbscooker.exe` 和 `sbsrender.exe`（D3D11）。输出在 `02_assets/textures/generated/architecture_sd`：**26 张 2048² / 16-bit PNG**，当前工程实际使用其中 21 张。未使用首版 Pillow 图作为 SD 输入或把旧图改名为 SD 产物。

该目录的 `manifest.json` 记录源 SBS/SBSAR、原生命令、输入/输出 SHA256、颜色空间、物理尺度及 OpenGL 法线。`07_pipeline/cache/architecture_rebuild/sd_*_cook.log` 与 `sd_*_render.log` 保留实际编译和输出日志。节点保持原名，解释放独立注释框。

棉麻源是既有 [ambientCG Fabric030](https://ambientcg.com/view?id=Fabric030)，**CC0**。SD 输入原始 Color、Displacement、Roughness，经过调色和物理法线处理生成最终材质，原始文件未改名、未覆盖。SBS 保留三路可替换 image input；重新渲染时，原文件绑定路径可从 manifest 的 `commands` / `inputs` 复用。扫描 tile 制作设定 0.25 m。BaseColor 使用 sRGB，其余数据图为 Non-Color。

布面使用漫透射 BSDF 与棉麻表面混合；没有使用玻璃折射模型或粗大透明洞假装布料。

## 后期动力学边界

每块主体预留 `Pin_Top_Hanging_Points` 和 `Tieback_Optional_Constraint` 顶点组。修改器顺序 `Cloth → Subdivision → Solidify`，厚度 0.75 mm。Cloth 的 viewport/render 均禁用，1001–1120 缓存**未烘焙**。读回程序实际遍历网格边，确认四块主体各只有一个连通分量。

这不是完成的微风动画。后续先设置束带碰撞/约束；**仅开启顶部 pin 的 Cloth，腰部会松脱**。若要完全自由帘，则隐藏或解开束带。启用前还需核对窗台、轨道、墙体碰撞、风力、时间步及局部穿插，再烘焙。整景替换应保持模拟关闭。

## 检查及恢复

`validation.json` 是最终 8 集合与实际 SD 依赖报告；`readback.json` 来自重新打开最终工程；`sd_dynamics_validation.json` 记录连续网格、pin 与模拟状态。21/21 贴图路径有效且均为 2K；8 个 pivot 保持；四块 Cloth 禁用且未烘焙。

六张 Cycles 64 samples / 1600×1200 图均已实际渲染并查看：窗帘完整形态、帘头、逆光材质近景，及门窗全部重新赋 SD 后的复查图。最终局部张力褶从首轮偏硬的幅度降为 5–8 mm，过渡加宽。

最终入景检查发现并修复窗玻璃镜面化：封闭盒形网格法线反向，使折射介质方向错误；同时新材质缺少旧布局的 shadow-ray 薄窗透光近似。已纠正 1,025 个反向网格，并为两种玻璃恢复仅 shadow ray 使用 Transparent 的分支；相机/反射射线仍使用 Transmission=1、IOR=1.46 的玻璃。未改场景灯光。重新打开源文件验证 1,114 个封闭网格均无负体积，两种玻璃分支正确，记录见 `glass_fix.json` 与 `readback.json`。

`architecture_glass_optical_test.py` 使用最终 SD 玻璃进行独立 CPU A/B 实渲，48 samples / 960×720：修复前重现镜面和不透直射，修复后可透见彩格并保留窗框细影。两图均已实际查看。测试不保存源文件、也不修改主镜头灯光；整景验证由整合线程另行完成。上面六张结构图是此法线修复前的构造评审，光学效果应以下图和最终整景为准。

![修复前的光学诊断](glass_optical_before.png)
![修复后的光学诊断](glass_optical_after.png)

首版恢复副本：`07_pipeline/cache/architecture_rebuild/architecture_first_pass_recovery.blend`。这是原工作文件副本，恢复时需复制回原工作路径以保持相对贴图路径意义。首版 authored 目录仍保留，最终工程不引用。不要重新运行首阶段 `architecture_rebuild.py` 覆盖最终 SD 工程。

![连续侧束窗帘](curtain_full.png)
![帘头织纹与吊挂](curtain_heading.png)
![棉麻逆光材质](curtain_transmission.png)
![双轨窗与月牙锁](window_structure.png)
![门模块](door_structure.png)
![金属把手与锁](door_hardware.png)
