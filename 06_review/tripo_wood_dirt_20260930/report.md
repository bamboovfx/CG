# 木椅表面小脏渍

2026-09-30：按用户新增三张近景参考，在上一版老化／磨损之后追加独立表面层。用户认为已有老化和磨损改善，本轮保留其节点、贴图及当前强度，没有重制工艺层。

## 当前结果

候选：[tripo_wood_dirt.blend](../../07_pipeline/cache/tripo_wood_dirt_20260930/tripo_wood_dirt.blend)。

新增内容是分簇的小深色点、灰褐附着残留和少量淡擦抹。污点的形状、尺寸、浓淡不同，有碎边和细小空缺；附着残留会同时影响颜色、粗糙度、基础／清漆法线与清漆响应。显著污点（蒙版>0.1）占座板纹理域约0.133%、靠背约0.111%，另外有更淡的擦抹。面积比例不是整模型的测量结果，而是4K位置图上的统计。

保持宽幅木纹、现有老化与磨损以及木板总体抛光感。附着物的Bump尺度为25µm，实际还乘高度图；不是大面积坑洼。木材Metallic保持原路径，没有把脏渍做成金属，也没有新增AO压暗。

## 参考与来源

用户提供的深色旧木近景约束细小污点、灰褐残留和稀疏分布；另外两张当前模型图用于对照现有磨损与整体颜色。参考照片只作观察，没有采样其像素。

细碎内容继续使用已有 [Poly Haven wood_table_worn](https://polyhaven.com/a/wood_table_worn) 的原始8K扫描颜色和粗糙度（CC0），来源／作者／哈希沿用 [源素材清单](../../02_assets/textures/external/polyhaven_wood_detail/manifest.json)。位置蒙版是本次按毫米尺度直接4096采样的技术图，再由原生SD结合扫描处理，原生源与重制方法见 [材质说明](../../02_assets/materials/tripo_wood_dirt/README.md)。

## 使用方式

座板 `LP_part_02`、靠背 `LP_part_09` 的材质内，默认节点名 `Group.002` 是独立表面脏渍组；注释框说明用途。其 `Dirt=1` 是当前候选，`Dirt=0` 返回用户最新保存的上一版。`Age=1`、`Wear≈0.95`、`Scratches≈0.95` 保持输入值。

新增组有4张实际使用的4K图：DirtMask／DirtColor／DirtRoughness／DirtHeight；另外导出ResidueMask与SmudgeMask供继续制作。颜色sRGB，数据图Non-Color。所有默认节点名和可见标题保持，解释写在注释框。

本轮输出独立脏渍图和分层Blender工程，没有将旧材质与新脏渍重新烘成统一最终五通道贴图。

紧特写检查后，单独压深附着物反照率，使亮布光下仍能读出小污点。DirtColor在线性空间乘(0.38, 0.44, 0.52)，保留扫描色差，不改位置、尺寸或原木材颜色。SD输出保留未经Blender该校色的目标图。

## 检查与证据

- [同光座面前后](seat_comparison.jpg)、[同光近景](macro_comparison.jpg)、[污斑紧特写前后](stain_comparison.jpg)、[脏渍图100%裁片](map_100_percent.jpg)。紧特写通过UV定位实际顶面，95mm透视镜头、2000²；[定位记录](stain_closeup.json)。
- 整椅：[05_after_whole.png](05_after_whole.png)；靠背：[04_after_back.png](04_after_back.png)。
- 保存后重开19项通过：工艺／原表现组摘要、控制值、木板几何／原UV／自定义法线保持；两个独立层都正确串接到BSDF；Metallic原路径保持；44张实际使用图全部打包；三盏灯与透视相机保持。详细证据：[reopen_validation.json](reopen_validation.json)。
- 两份SBSAR的Dirt=0时DirtMask／DirtHeight全零；两板实际输出4096²并有非零细节变化。Blender归零同机位渲染与加层前最大差1个8位值，平均差约0.000072832，无像素差超过2。详细证据：[sd_validation.json](sd_validation.json)。
- 输入是用户在21:38保存的最新候选，SHA256 `e23e4e97a1caaa1bf8cc33ffa36fd2169830b96a4c59e7817aa34ae03dfe7e6a`，本轮输入未覆盖。当前新候选SHA256 `336216ae8fd841e013d465bb83827a29daa42f182f31b9126b069de095207710`。保存记录：[validation.json](validation.json)。
- 评审图为Cycles、128 samples、AgX、原工作室三点布光；座面／整椅1400²，特写2000²。

技术通过；新增小脏渍的密度、颜色和参考接近程度待用户视觉审阅。没有替换教室主镜头。
