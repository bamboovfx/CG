# 教学陈设重做评审 · 2026-09-11

24 个教学集合已完成独立源工程，保留旧集合名、instance_offset 和安装包络。源文件为 [classroom_teaching.blend](../../02_assets/work/classroom_teaching.blend)，导入时排除 `Teaching_review_rig`。

原片已实际查看 154s、160s、166s、168s：绿色空黑板、木色细框与粉笔槽、浅色讲台正面、电视旁窄高暖木书架。背后连接与看不清的五金属于制作设定。实物照片只用于观察结构，没有烘焙进材质。

## 结构与材质

- 黑板：独立背衬、写字底板、内侧阶梯压条、横竖木框接缝，开口槽形粉笔槽、端盖、支架和螺钉。圆柱粉笔、木柄加独立毡条的板擦、细小不规则积粉。4K SD 原生擦痕、细粉与粗糙度变化保留空板感觉。
- 讲台：浅色贴面正面、侧板木封边、两层工作搁板、内侧连接条与托片、内凹踢脚、厚实圆边台面。正面朝学生 -Y；工作搁板朝 +Y。
- 教师边桌：真实横向撑杆、独立包脚、台面底托、分段前围板和抽屉开口、薄抽屉底与侧板、弯管拉手；抽屉开向 +Y。
- 书架：35mm立板、23mm层板、薄背板、独立前封边、层板销与承托、调节孔、内凹底座。纹理按板件长边定木纹，用 CC0 Poly Haven 4K 木纹作为 SD 输入，经过清漆、划痕、粗糙度及局部露木处理，物理周期0.5m。
- 10 本竖书：独立圆角硬封皮、曲面厚书脊、18组书帖、堵头布、贴合弧面的纸标；保留不同高度并调整为砖红、蓝灰、浅绿、深绿等低饱和变化。
- 5 本横放练习册：上下厚封皮、胶装书脊、12组页片、细缝线、空白贴签。
- 5 张公告：0.16mm纸厚、连续弯纸网格、不同卷角、图钉贴纸面；图案只保留不可辨识的淡灰线段，不编造原文。

材质已改为真实 Substance Designer 流程：6 个原生可编辑 SBS、6 个实际编译 SBSAR、10 套共54张实际导出的16-bit PNG。木材和黑板4096×4096，纸/布/毡/5张公告2048×2048；另外复用设备组 enamel、metal、dark 三族 SD 输出。源工程共55个有效图像依赖，颜色图sRGB，其余Non-Color，OpenGL法线。木纹来自 CC0 扫描，其他表面是 SD 原生生成器；公告只读取项目原创淡线图作为油墨输入，不保留旧程序纸面。完整命令、输入路径与输出哈希见 [SD清单](sd_delivery.json) 和 [导出记录](../../02_assets/textures/generated/teaching_sd/manifest.json)。

## 已检查和修正

实际完成两轮10张GPU近景并逐张查看。修正了书脊纸标被曲面遮住、图钉柄伸出纸面、粉尘方块感及评审取景裁切；教师桌另加一次渲染，修正了围板挡住抽屉的问题。SD接入后再次渲染10个视角并实际查看；随后收窄并打散木材边缘露木、增强黑板的局部擦痕对比，露木混合再收至0.30并补渲相关6个视角。SD接入后再次渲染10个视角并实际查看；随后收窄并打散木材边缘露木、增强黑板的局部擦痕对比，露木混合再收至0.30并补渲相关6个视角。最终没有贴图丢失或无贴图材质。

24个offset逐分量相等，评估后的最大包络偏差0.031mm。数据详见 [validation.json](validation.json)，材质来源和哈希详见 [asset_manifest.json](asset_manifest.json)。这些是独立资产检查，不代表整景光照或原片复刻已完成。

## 入景接触修正

旧竖书共用同一中心高度，底面实际不齐，原来存在悬空/穿层板；横书原栈间距也偏大。源集合包络按约定保留，**入景时将 [book_contact_corrections.json](book_contact_corrections.json) 中的 `instance_delta_z` 加到对应书籍实例的 Z**。书架顶层承托面1.0165001m、中层0.5315000m。评审书架图已临时应用该接触修正，未改源集合。

## 渲染

![黑板](board.png)
![粉笔槽和板擦](board_tray.png)
![讲台正面](podium_front.png)
![讲台工作面](podium_back.png)
![教师边桌抽屉侧](teacher_table.png)
![书架与书籍接触](bookshelf.png)
![书脊封皮页块](books.png)
![练习册](notebooks.png)
![公告](notices.png)
![公告图钉接触](notice_corner.png)

## 实物参考

[木框黑板槽部实物](https://www.webstaurantstore.com/aarco-oc2436b-24-x-36-black-solid-oak-wood-frame-slate-composition-chalkboard/116OC2436B.html) · [昭和教卓实物](https://f-kasugai.seesaa.net/article/2017-03-21.html) · [Poly Haven plywood](https://polyhaven.com/a/plywood)

![粉笔槽实物参考](references/oak_board_tray.jpg)
![教卓实物参考](references/showa_teacher_table.jpg)

## 材质近景参考

以下照片实际打开查看，仅用来判断清漆磨损、粉笔擦痕和纸纤维，不作为贴图像素来源。

[Worn beech school desk varnish close-up](https://www.mustardvintage.com/products/mid-century-rustic-beech-school-desk-1708d)

![Worn beech school desk varnish close-up](material_references/worn_beech_varnish.jpg)

[Erased chalkboard mineral residue close-up](https://www.goodfreephotos.com/other-photos/chalkboard-blackboard-with-eraser-marks.jpg.php)

![Erased chalkboard mineral residue close-up](material_references/erased_chalk_surface.jpg)

[Wagamido paper fibre close-up](https://www.wagamido.jp/product/928)

![Wagamido paper fibre close-up](material_references/paper_fibres_closeup.jpg)

