# 木椅侧立面与背面异常修复

2026-09-30：按用户标注的侧立面条带／拉扯与背面矩形，读取最新已保存候选，并核对当前Blender实例。修复已应用到当前打开的模型，另存为 [tripo_wood_side_back.blend](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)，原输入文件保持。

## 查明的原因与修复

侧立面原材质 `Reference wood / plywood edge` 只读取局部厚度轴，经正弦函数生成颜色，没有横向木纤维或细碎变化，因此出现整齐、贯穿整圈的等宽横条。它并没有读取UV，所以截图中最明显的条带不能归因于UV采样拉伸。

此外，正面专用的 `UV_WoodReference` 平面投影在侧壁上确有退化：座板239个侧壁三角形中190个，靠背198个中88个UV面积接近零。原侧边材质不用这套UV，但它不适合拿来贴侧壁纹理。本轮保留正面／烘焙UV，新增按实体周长×厚度计算的米制 `UV_WoodEdge`，让侧壁材质明确读取该图；移除原来的单轴正弦条带，改成不规则薄层和细碎切口纤维，配合浅表粗糙度及22µm尺度微凹凸。

新的UV覆盖全部实际侧壁，437个三角形无退化，面积映射比座板0.861–1.000、靠背0.892–1.000；独立重开验证还检查了局部Jacobian的长短轴比例，防止只用面积掩盖拉伸。该图以1UV单位=1米供实时程序材质使用，不是重新打包的0–1最终贴图图集。现有正面／烘焙UV和法线切线基保持。

背面的矩形来自早期制作的 `StampMask`，并非UV或法线问题。早期脚本在UV矩形 `0.48<u<0.77`、`0.25<v<0.41` 内，用两组正弦和噪声生成模拟旧印记；后续材质一直继承了 `rear_stamp_preserved` 颜色混合分支，所以表现为一片规则网格。该合成印记没有真实文字或结构依据，本轮关闭它的颜色Factor，旧资源保留作来源记录，不再进入材质输出。老化、磨损、划痕与小脏渍分支继续保持。

## 证据

- [侧立面前后](side_comparison.jpg)、[背面前后](back_comparison.jpg)、[转角前后](corner_comparison.jpg)。
- 单独关闭印记后的 [背面隔离图](04_back_stamp_off.png) 已消除矩形；最终背面图仅有侧边材质与间接光的小差异，验证了矩形来自颜色分支：[isolation_comparison.json](isolation_comparison.json)。
- 原始异常路径在2秒级只读诊断中可重复复现：[probe_before.json](probe_before.json)。最终文件运行同一诊断 `--require-clean`，两种异常均为false：[probe_after.json](probe_after.json)。
- 保存后重开23项通过：顶点／面／全部已有UV／自定义法线、工艺组、小脏渍组、Age／Wear／Scratches保持；实际侧壁UV连接、无退化与拉伸范围、印记Factor断开、44张节点引用图打包正确。局部最大长短轴比例座板1.162、靠背1.121：[reopen_validation.json](reopen_validation.json)。
- [正面修复前](03_top_before.png) 与 [修复后](08_top_after.png) 的表面组保持，侧截面按本轮要求改变；没有重新生成底层木纹或表现贴图。

渲染为固定机位、原三点布光与色彩管理，Cycles 96 samples；前后图1600×1000，正面图1400²。当前用户的视口与其它设置保持，修复另存后Blender未处于未保存状态。没有替换教室主镜头。

输入SHA256 `d6ae50afde51a9df2366b59ce06fa032dd9492b07e4bc7fa802968fc166eb9f9`；当前修复版SHA256 `8f41b3e646edd06a04ad8d3327aa37d393a7a7de0743ce7a6e1812c9b5e27266`。实际保护摘要与侧壁统计：[validation.json](validation.json)。

复现／维护入口：`07_pipeline/scripts/fix_wood_side_back.py`；只读诊断 `probe_wood_side_back.py`；重开检查 `validate_wood_side_back.py`。技术修复通过，同视角材质外观待用户审阅。
