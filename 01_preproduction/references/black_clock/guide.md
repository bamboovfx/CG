# 黑色钟表：参考与手动修改 · 2026-09-14

本轮只搜集参考、读取当前模型并讲解，没有改动 Blender 场景。以下参数是待渲染验证的制作起点，不是已经完成的效果。

## 实物参考

### 1. 黑色外圈的柔和高光

![Seiko 黑色外圈近照](seiko_black_bezel_detail.jpg)

[原页面：Pamono / Seiko](https://www.pamono.com/vintage-black-wall-clock-from-seiko-1990s-1)。观察卷边上的宽高光和深灰黑表面；款式和年代依卖家描述，不据照片断言精确材料。

### 2. 黑壳与银色五金的区分

![Seiko 黑壳与银圈](seiko_black_case_silver_rim.jpg)

[原页面：Catawiki / Seikosha](https://www.catawiki.com/en/l/77342509-wall-clock-seikosha-bakelite-glass-plastic-steel-1980-1990)。参考黑壳、银圈、外露闭合五金的层次。照片是侧面闭合结构，并不证明当前模型两颗正面螺丝的摆位正确。当前模型保留两颗正面螺丝属于制作选择。

### 3. 偏哑光的黑漆金属壳

![Newgate 哑黑金属钟](newgate_matt_black_metal.jpg)

[原页面：Newgate Universal Black](https://newgateworld.com/collections/wall-clocks-dial-type-marker/products/newgate-universal-wall-clock-in-black)。厂家标注金属壳、哑黑表面，可参考宽浅高光和清楚的侧壁厚度。

以上照片版权归原网站/摄影者，仅作项目参考，不用于贴图，不标为 CC0。

## 推荐的外观分配

- `Depth clock spun enamel case`：半哑光黑漆。
- `Depth clock rolled bezel`：同一黑漆。
- `Depth clock inner polished return`：保留细银色金属圈。
- 两颗 `Depth clock bezel closure screw`：保留银色。
- 表盘：保留米白色，指针和刻度保持可读。

上一张截图里的材质 `Depth / Clock brushed steel rim` 用于银圈和螺丝，并不是目前米白外壳的材质。真正外壳材质是 `Depth / Clock aged enamel`，目前由三个部件共享。

## 先在可编辑的源工程练习

当前镜头中的钟表来自链接库，直接在镜头文件中修改会受链接限制。源工程：`D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_equipment.blend`，集合 `AST_wall_clock`。

在另一个 Blender 窗口打开源工程可保留当前镜头窗口。以下步骤在源工程操作。源文件保存不会自动更新镜头：正式应用还需要同步到 `02_assets/library/classroom_assets.blend`，随后在镜头的 Outliner / Blender File / Libraries 中重载该库。当前的源工程与库是分开发布的两个文件。

## 改黑色漆面

1. 选择 `Depth clock rolled bezel`，在材质栏找到 `Depth / Clock aged enamel`。
2. 点击材质名称旁的用户数量按钮，复制为单独材质，命名 `Clock black enamel`。这样不会把共用的内侧托盘一起改黑。
3. Shader Editor 中断开接入 Principled BSDF 的 Base Color、Metallic、Roughness 的连线，先直接设置基础效果：

| 输入 | 起始值 |
|---|---|
| Base Color | 颜色拾取器 Hex：`#242424`（sRGB），约等于线性 RGB 0.0176 |
| Metallic | 0 |
| Roughness | 0.30 |
| IOR | 1.50 |
| Coat Weight | 0.12 |
| Coat Roughness | 0.24 |
| Anisotropic | 0 |

这些是本镜头建议起始值，不是从参考照片测量的物理参数。保留现有 Normal/Bump 链。黑漆是覆盖在金属上的不透明漆层，不能因底层是金属就把其表面 Metallic 设为 1。

4. 选择 `Depth clock spun enamel case`，从材质下拉列表选择同一份 `Clock black enamel`。
5. 确认基础黑色后，再保留原有粗糙度变化：把之前接入 Roughness 的旧输出经过一个 Map Range，From 0–1、To 0.26–0.40、Clamp 开启，再接回 Roughness。这样保留变化但避免旧污渍分支的 0.74 使黑壳局部过度发粉。

如果还想保留底色的轻微斑驳，可让旧底色输出经过 Color Ramp，两个颜色设为 `#202020` 与 `#292929` 后接 Base Color。变化保持克制，先观察高光再增加污旧程度。

## 修复两颗螺丝被外圈遮住

对当前场景几何做了沿全局 +Y 的射线检查：螺丝所在位置的外圈正面 Y≈4.36825 m；螺丝头正面 Y≈4.376 m，埋在外圈后面约 7.75 mm。朝教室/钟表正面的方向为全局 −Y。这是之前建模时没有对齐新的卷边剖面，不是渲染隐藏。

在 Object Mode 同时选中这四个对象：

- `Depth clock bezel closure screw`
- `Depth clock bezel closure screw.001`
- `Depth clock screw slot`
- `Depth clock screw slot.001`

把 Transform Orientation 设为 Global，鼠标移到 3D View，执行 `G` → `Y` → 输入 `-0.009` → Enter。只执行一次。这会同时将两个螺丝头及其槽口向正面移动 9 mm，使螺丝头在中心位置高出壳面约 1.25 mm，而后部仍嵌在外壳内。

这两个黑色槽口目前是单独的薄几何件，因此必须随螺丝移动。不要只移动银色螺丝，也不要整体后移或缩小外圈，那会影响它与玻璃、密封圈的配合。

最后从正面和侧面检查：两颗螺丝均露出；槽口位于螺丝头表面；螺丝根部没有悬空。9 mm 数值只适用于这里已核对的源模型方向和几何，如果期间改过外圈剖面，应重新按表面对齐。

## 按新参考做擦拭痕与指纹

用户补充的黑色表面照片，明暗包含拍摄时的照明。它适合定义外观方向，不宜整张直接作为 Base Color，更不能当成准确的 Height。希望获得的是：深黑底色，斜角反光时浮现的擦拭印和指纹，以及极细的表面划痕。

先用前述黑漆基础值。底色保持 #202020–#292929 的小幅变化，主要纹理放到 Roughness：

```text
指纹/擦拭遮罩 Image Texture（Non-Color）.Color
    → Map Range.Value
Map Range：From Min = 0，From Max = 1
           To Min = 0.27，To Max = 0.43，Clamp = 开启
Map Range.Result → Principled BSDF.Roughness
```

这条分支替代上面的旧粗糙度试验分支，不能把两条同时连接到同一个输入。遮罩白色区域在这个设定下更粗糙；油印有时更光滑，可交换 To Min/Max 后对照观察。指纹按约 1–2 cm 的现实尺度铺设，集中在侧壳和可抓握外圈，避免整圈均匀重复。普通 Noise Texture 不会自行生成指纹脊线或擦拭轨迹，需要有对应形状的遮罩。

保留细微 Normal/Bump。指纹主要改变反射，不做肉眼可见的几何置换。Coat Weight 先用 0.05–0.12；过强的均匀清漆高光会掩盖下层的粗糙度差异。若确实需要清漆层，可让同一遮罩另经 Map Range 0–1→0.20–0.34 接 Coat Roughness。近景应看到痕迹，完整镜头主要读出黑壳轮廓和柔和高光。

## 三个前墙物件的明度分配

建议钟表深黑，电视机壳炭灰，音箱外框深灰棕。三个东西不必都设为同一个黑色。以下 Hex 是 sRGB 基础颜色起点：

| 部位 | Base Color | Roughness 起点 | 表面解释 |
|---|---|---|---|
| 钟表外壳 | #242424 | 0.27–0.43 | 黑漆，Metallic 0，细银圈与螺丝保留金属 |
| 电视机壳 | #373936 | 0.35–0.48 | 深灰旧塑料，Metallic 0，屏幕另用玻璃材质 |
| 音箱外框 | #45433E | 0.40–0.52 | 深灰棕涂层，网罩与内部黑腔仍分开 |

电视外壳当前材质为 `EQ SD enamel closeup AST_crt_television`。音箱网罩部分使用 `EQ SD enamel.001`，内部挡板使用 `EQ SD dark.001`。按对象的材质槽核对后复制专用材质，不要全局改所有 enamel 材质，也不要将玻璃或内部黑腔一起替换。

## 室内绿色、走廊蓝色与冷暖照明

已核对：两侧不是共用一份墙面材质。现有 `Mix (Legacy)` 是 Multiply，Factor 为 1，代表纹理与 Color2 完整相乘，不是直接用 Color2 覆盖纹理。

| 当前材质 | Color2 当前线性 RGB 乘数 | 观察 |
|---|---|---|
| Surface / SH SD sage mineral wall.001 | 0.62, 0.86, 0.97 | 室内上墙 |
| Surface / SH SD warm grey dado.001 | 1.40, 1.22, 1.55 | 室内下墙，三个通道均被提亮 |
| Surface / COR SD aged school plaster | 1.10, 1.10, 1.06 | 走廊上墙，近中性且提亮 |
| Surface / COR SD grey green lower wall | 0.63, 0.70, 0.65 | 走廊下墙，仍是灰绿色 |

为了更直观地指定墙色，可只替换 Base Color 分支，保留已经完成的 Roughness、Normal、Displacement：

```text
原 Base Color Image Texture.Color → RGB to BW.Color
RGB to BW.Val → Map Range.Value
Map Range：From 0–1 → To 0.85–1.05，Clamp 开启
Map Range.Result → Mix (Legacy).Color1
Mix (Legacy)：Multiply，Factor = 1
Mix (Legacy).Color2 = 所选墙面基础色（用颜色拾取器 Hex 输入）
Mix (Legacy).Color → Principled BSDF.Base Color
```

这样原贴图提供克制的斑驳变化，新的基础色决定主色调。会舍弃旧贴图的彩色污迹，若其色差需要保留，优先在原 Multiply 上小幅校色。不要直接把下表 Hex 当成旧节点的乘色后期待同样结果。

| 区域 | 建议基础色 Hex（sRGB） |
|---|---|
| 室内上墙 | #566B59，较深的灰绿 |
| 室内下墙 | #B2AA95，暖灰米色 |
| 走廊上墙 | #637E91，蓝灰 |
| 走廊下墙 | #475F73，较暗蓝灰 |

先固定曝光和现有日光，查看墙色的效果；再调整走廊天空填充。保留室内斜射暖阳及其窗口投影，让走廊主要接受偏冷的天空散射光。若需要补光，使用放在走廊外侧、朝走廊的较大 Area Light，颜色从低饱和蓝灰开始；功率根据走廊的实际亮度调，保持走廊比教室受光面暗。以位置、朝向和遮挡限制它，不要让冷补光冲淡整个教室，也不要把整个 World 或白平衡一并调蓝。

当前单独的 `lgt_sun_afternoon` 已关闭渲染，照明使用 World 的 daylight 网络。只改变这盏关闭的 Sun 不会改变最终渲染，也不要直接开启它叠加一份太阳。通过已有 daylight 控制调整太阳方向；冷暖分区用走廊受光与独立墙色来建立。

验证顺序：全景看钟表/电视/音箱是否能从墙面分开；彩色看教室暖阳与走廊冷影；再用钟表近景观察擦痕是否只在合适的反光角度出现。一次只改变一组参数，防止用曝光补偿材质问题。
