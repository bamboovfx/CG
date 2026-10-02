# 薄边黑色挂钟重做 · 2026-09-14

依据用户提供的正面与斜侧参考图，替换原来过厚后壳和圆滚外圈。当前镜头的相机、布局与灯光保持原样。

- 直径 374 mm；总厚度 55 mm；前沿宽约 3.5 mm。
- 黑漆直侧壳、背面轻微收窄、窄内侧压条、2 mm 平面玻璃、独立密封圈、米白表盘。
- 12 个沿圆周旋转的 Arial Narrow 数字，60 个刻度，分层黑色指针；时间约 10:10:05。
- 去掉旧款正面的两颗装饰闭合螺丝和粗圆环，与新参考保持一致。
- 黑漆用独立微表面纹理和弱粗糙度变化；此次以轮廓和参考比例为重点，未制作强烈指纹或大面积掉漆。
- 用户此前创建的 `Depth / Clock black enamel` 保存在源工程中，设置保留标记。新壳实际使用 `Clock / Reference black enamel`，旧练习材质没有被覆盖。

已渲染并查看正面、斜侧面、教室全景。第一轮将数字进一步放大，并收窄内侧亮边。几何检查为 12 个数字、60 个刻度；源工程与资产库的非钟表对象变换、网格顶点数量、材质分配一致，未发现丢失图片。全景的小尺寸主要读到轮廓和表盘，近景用于检查壳体厚度及玻璃层次。

![正面](../04_renders/sq010/sh010/clock_slim/v001/front.png)
![斜侧面](../04_renders/sq010/sh010/clock_slim/v001/oblique.png)
![教室](../04_renders/sq010/sh010/clock_slim/v001/classroom.png)

## 文件

- 源工程：`02_assets/work/classroom_equipment.blend`
- 资产库：`02_assets/library/classroom_assets.blend`
- 已在当前镜头重载并保存：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 源工程/库原文件恢复副本：`07_pipeline/cache/clock_slim_rebuild/source_before.blend` 和 `library_before.blend`。恢复时复制回原目录以保持原有相对路径含义。
- 校验、图像哈希和镜头合并记录：同一 cache 目录内 `published.json`、`visual_review.json`、`live_merge.json`。

源工程若仍在另一个旧窗口中打开，需要重新打开磁盘上的更新文件，以免旧窗口保存时覆盖新版。数字字体引用本机 `C:/Windows/Fonts/ARIALN.TTF`；此项为已验证存在的跨盘字体依赖。
