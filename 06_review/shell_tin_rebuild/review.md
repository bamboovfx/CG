# 房间壳体与糖果罐复核

固定源：`02_assets/work/classroom_shell_tin.blend`。包含 `AST_classroom_shell`、`AST_candy_tin`，原有 pivot 保留。

地板按原片 02:32/02:34 的交替方向拼木重建。制作尺寸采用 303 mm 方格、五根木条，来自 [toolbox 实物规格和材质近照](https://www.r-toolbox.jp/store/product/1355/)，是制作设定，不声称测出了影片尺寸。木条厚 17 mm，0.64 mm 拼缝与小倒角，地面顶标高保持 20.5 mm，桌椅接触不变。

实际看过 toolbox 无涂装木纹和着色表面，以及 [旧地板的清漆磨损](https://www.houzz.com/discussions/6154363/staining-parquet-flooring)。参考图只用于判断表面，未作为贴图。纹理输入使用项目既有 Poly Haven CC0 plywood 扫描，SD 添加棕色清漆、粗糙度分区和细划痕；不能把它说成影片地板扫描或已确认的橡木种类。首版原生纤维过弱，已改扫描输入并将模型上法线强度降至 0.30，避免磨损表现成粗糙起伏。

门口右侧矮墙和踢脚线按 Y=2.7375–3.9625 m 留空，与门窗组对齐。墙体使用 SD 矿物涂料细表面、分板缝和踢脚线收口。大布局、窗洞、室外体块不变。

糖果罐补圆角薄壁铁皮、端板压筋、卷口、接合缝与带截面的伸缩盖。包络仍约 103.4×63.4×121.2 mm，原167个罐体实例姿态不变。保留既有原创印刷图，通过 SD 添加细微掉墨、裸锡反射和粗糙度变化；它并非影片品牌印刷的精确复刻。后续刚体需另建简化碰撞代理。

SD 原生可编辑源与 SBSAR 位于 `02_assets/materials/shell_tin_rebuild`；5个材质族25张输出，木地板4K，其余2K，16bit，OpenGL normal。输入路径、输出哈希和真实编译/渲染日志分别见 `textures/generated/shell_tin_sd/manifest.json` 与 `07_pipeline/cache/shell_tin_rebuild/*_cook.log`、`*_render.log`。

已实际查看 `floor.png`、`tin.png`，确认拼木方向、实体拼缝、印刷方向和卷边。静态材质仍需与全景侧光一并评估，不能仅以面数和分辨率证明影片匹配。
