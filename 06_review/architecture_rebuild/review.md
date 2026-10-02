# 首版建筑模块记录 · 已被 SD / 连续窗帘修订替代

**最终交付请看 [review_sd.md](review_sd.md)。本页保留首版历史记录；Pillow 材质、拆分缝边和居中束帘不再用于最终工程。**

源工程：`02_assets/work/classroom_architecture.blend`。8 个 AST 集合保持原库 collection instance_offset，几何位于原来的世界坐标，直接替换集合实例即可。`ARC_preview` 仅用于评审，不应入资产库。

## 参考证据及判断

- 实际查看原片 `drop_official_1080p.mp4` 的 154、160、168 秒帧。160 秒可辨左侧浅色窗框、窄压条、大面积透明主窗和上亮，右侧蓝色高窗、灰白窗框和入口；168 秒可辨自然垂直帘褶及束拢位置。原片是画面比例、色调和安装位置的权威。
- [UR Community 窗户构件与五金实物图](https://www.ur-cm-support.jp/glossary/tabid135.html)：已下载并实际查看 `reference_window.png`，用于核对上下窗、双轨窗扇的搭接、月牙锁、窗框密封条与帘轨滑块。仅作造型参考，未进入材质。
- [TOSO C 型轨构件与安装图](https://item.rakuten.co.jp/auc-interia-kirameki/tocr-pa-cg-scrunner/)：已下载并实际查看 `reference_track.jpg`。滑块轮体、吊环和 C 型型材的材料不同；构图上保留原来的长轨位置，制作设定为每 0.56 米一支架。仅作造型参考。
- [Lilycolor 窗帘标准缝制图](https://www.interior-nagashima.com/product/item/id/343807/)：搜索结果显示双折侧边和褶头规格；图像下载遇到网站 EOF，未将其当作已下载/已检查素材。
- 窗扇壁厚、具体锁型号、门框截面及帘布精确尺寸无法从原片确认，均是适应现有模块尺寸的制作设定，不宣称一比一测绘。

## 几何处理

- 左窗：按原有开口重建，不改变总窗带位置。双轨错层窗扇、独立透明 5 mm 玻璃、EPDM 密封线、两侧可拆压条、月牙锁轴/凸轮/把手/锁扣、暗位指槽、挡块、排水孔及雨罩。高窗有独立小拉手。
- 走廊窗：保留蓝色高窗和中间横档；低位窗扇/窗台在门洞 `Y = 2.7375..3.9625 m` 处断开，修复原模型门与窗重叠。镜头 shell 的下墙和踢脚线也应在同范围留洞。
- 门：独立框梃、横档、真实可透光的隐私玻璃、胶条、压条、凹入下嵌板、拉手底板及回弯管、锁芯、分段合页轴节、门槛。保持原开合方向：合页在 +Y，把手在 -Y，室内面为 -X。
- 帘轨：由顶腹板、侧壁和内卷唇组成空心 C 截面，端帽、折弯悬臂、固定座、夹件及螺丝独立建模。
- 四块帘布：不等距主褶与重力方向细褶，束带处平滑压缩；主体厚 1.1 mm；实际平面双折边代替圆管边，底部约 100 mm 双折，顶部加固带、缝线、吊钩口袋、金属弯钩和滑块。一条有宽度的编织束带包围帘布，各片有不同相位。

## 贴图与依赖

- 帘布复用项目已有 [ambientCG Fabric030](https://ambientcg.com/view?id=Fabric030) 2K 扫描，CC0。原始文件名保持，使用 Color（sRGB）、Roughness（Non-Color）、NormalGL（Non-Color）；未使用 DirectX 法线。UV 为展开布长的米单位，贴图 tile 制作设定 0.25 m，保留细纤维而不过度鼓起。
- 新增 7 张确定性 2K PNG 微表面图，目录 `02_assets/textures/authored/architecture_rebuild`。属于 NumPy/Pillow 编写的材质纹理，不是扫描、不属于生成式 AI 图像。种子 91126；来源与哈希见 `provenance.json`。
- 烤漆：0.4 m tile，低对比清洁差异、细微橘皮；拉丝铝：0.2 m tile；玻璃：1 m tile，粗糙度约 0.038，使用 16-bit PNG 保存极低对比变化，避免量化后在门玻璃上放大成色斑。门隐私玻璃另以粗糙度 remap 提高漫透射。
- 所有 Shader 节点保留 Blender 默认名字与可见标题，材质自定义属性记录尺度。图像路径相对化。`validation.json` 记录全部集合映射、pivot、包围盒、面数、贴图颜色空间/尺寸/哈希。

## 验证

自动检查：8 集合原点逐分量相同；全部实际引用贴图存在且最小维度 2048；源工程只含此 8 个资产集合和评审灯光相机。近景渲染与视觉检查另见同目录图片及最终 readback 报告。

已完成 Cycles 64 samples / 1600×1200 实际渲染并逐张查看：`window_structure.png`、`curtain_full.png`、`curtain_heading.png`、`door_structure.png`、`door_hardware.png`。首轮检查后修正了后轨锁遮挡、帘布偏灰、缝线过粗、管件折角和门顶留缝；最终图已覆盖为修正版。前端最后一片帘布的顶部向轨道内收 145 mm，滑块不越过轨道端帽。最终重新打开工程，10/10 实际外链存在且均为 2048²。无缺图。

![窗锁与双轨](window_structure.png)
![帘布与束带](curtain_full.png)
![加固帘头及吊钩](curtain_heading.png)
![独立门模块](door_structure.png)
![锁与回弯拉手](door_hardware.png)
