# 糖果罐与设备接触磨损，2026-09-12

修改源：`02_assets/work/classroom_shell_tin.blend` 仅替换 `AST_candy_tin`。建筑壳体对象矩阵、网格坐标、材质身份的前后 SHA-256 相同；没有编辑正式库、镜头或 167 个实例。保留项目既有原创 DROPS 图案，并非原片商品标识的精确复刻。

罐体外包络 103.394 × 63.390 × 121.200 mm；集合 instance_offset 为 (0,0,0)，主体前面 -Y。结构包含 0.22 mm 成型侧板、0.25 mm 冲压端板、真实开口颈、具有折叠截面的双卷封边、独立压入式盖、后侧折合接缝、0.12–0.23 mm 两处宽凹痕。印刷几何随罐体弯曲，50 μm 渲染间距用于避免交叠，并非声称油墨厚度。没有圆角盒子加孤立凸点的旧盖结构。基础网格共 37,648 面，16 个可见零件。

三套独立 4K 原生 Substance Designer 材质：`hero_tinplate`、`hero_lithographic_ink`、`hero_red_lacquer`。实际 sbscooker 编译及 sbsrender 16 位输出，包含慢尺度氧化/触摸光泽、方向性轧制痕迹、细划痕与稀疏油墨磨损。金属导体只在裸露金属区域；油墨上有单独透明清漆。工程新增 2K `equipment_contact_film` 原生 SD 接触膜作为局部反射粗糙度，不把指纹涂进 BaseColor。全部 Blender 节点保持默认名称及空 Label。

实际查看的评审：`hero_front.png`、`hero_lid_macro.png`、`hero_back.png`，CPU Cycles 40 samples、1000 px。检查后修正了两轮印刷曲面穿插和端板平面法线引起的软枕高光。细微划痕主要在近景和掠射光可见，未做全表面随机脏点。

参考已实际查看：原片 158 / 164 / 168 秒帧；山星屋所藏七福糖果罐与 1993 年左右的五种サクマ式ドロップス实物照片。图库照片只作外形与漆膜参考，没有用于纹理采样，版权归原摄影/收藏方。原片 168 秒显示红白印刷与金属端面反光，尺寸沿用已布置资产，不按实物照片重新缩放。

- 图文来源：https://okashi-to-watashi.jp/post/1728
- `references/museum_tin_reference.jpg`：https://okashi-to-watashi.jp/img/posts/upload/⑦七福ドロップス.jpg
- `references/sakuma_five_tins.jpg`：https://okashi-to-watashi.jp/img/posts/upload/④サクマ式ドロップス　５種.jpg
- 木材扫描仍为 Poly Haven plywood，CC0：https://polyhaven.com/a/plywood；旧目录原始 4K 文件、来源和哈希保留。

SD 源、SBSAR、输入作品 SHA、导出 PNG SHA、色彩空间和精确命令见 `02_assets/textures/generated/hero_tin_sd/manifest.json`；编译日志在 `07_pipeline/cache/equipment_rebuild/hero_tin`。BaseColor 为 sRGB，Roughness/Metallic/Normal/Height 为 Non-Color，OpenGL normal，物理纹理尺度 12 cm。原始图案分辨率 2K，经过原生 SD 表面处理输出 4K，不声称图案本身获得了额外的原始图形细节。

动态准备：`DYN_candy_tin_collision` 是独立集合，含一个 56 顶点 / 108 三角面、封闭且凸的低模代理，隐藏渲染。它不在 `AST_candy_tin` 内，避免每个可见实例自动带入代理。集成时单独 append 此集合，后续动态测试再按既有 167 实例矩阵复制代理并绑定可见实例。当前没有启用任何 rigid body 或改变动画。建议空罐质量 0.09 kg、含假设 120 g 糖果时 0.21 kg、碰撞余量 0.3 mm；这些为制作估计，未测量原片道具。摩擦 0.45 / 弹性 0.12 仅为后续试算起点。

设备源 `02_assets/work/classroom_equipment.blend` 修改集合为 `AST_equipment_cabinet`、`AST_crt_television`。木柜 SD 清漆加琥珀吸收，接触层集中在把手、下横档清洁区与电视脚周围；上缘增加 18 条极细木纹方向擦痕，并打散把手旁原先规整的露木片。TV 塑料加局部年龄色差，凸屏下角只有微弱擦拭残迹。其余三设备及安装位置不变。

安全恢复点：`07_pipeline/cache/equipment_rebuild/hero_tin/before_hero_tin.blend` 与 `07_pipeline/cache/equipment_rebuild/before_contact_age.blend`。候选缓存也保留。验证包括源文件被其他人修改的 SHA 检查、缺失依赖、相对路径、节点 Label、未启用动力学和集合包络。具体结果见同缓存下 `hero_tin/validation.json`、`hero_tin/readback.json`、`contact_age_validation.json`、`contact_readback.json`。
