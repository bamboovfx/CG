# CRT 电视建模重做 · 2026-09-14

以用户提供的日立 CRT 实物照片作为外形主参考，结合两组 ArtStation 作品补充装配结构。电视仍使用原教室资产集合 `AST_crt_television`、原枢轴和柜面接触高度。照片里的推车未纳入此次重做。

## 参考如何使用

- [Jyotirmay Dubey — Old TV](https://www.artstation.com/artwork/DvQ9Dn)：已查看正面和斜侧面，参考内凹屏幕框、深机壳与底部控制仓。
- [Sahaar Chhabra — Retro CRT 90’s Monitor](https://www.artstation.com/artwork/nE129e)：已查看前后面组合图，参考后部检修面板、分组散热孔、螺丝座、接口和铭牌。未照搬专业监视器的外形。
- 实物照片归档于 `01_preproduction/references/tv_reference/user_hitachi_crt.png`；来源和使用方式见同目录 `references.json`。没有下载或复制作者的模型、材质。

## 本次实现

- 方正窄圆角的前框、独立玻璃压边与前后壳分型缝。
- 略鼓的 CRT 玻璃、5 mm 玻璃厚度与后方独立深色荧光屏；保持关闭状态。
- 前后有区别的外壳轮廓：较直的前侧壁、逐级收窄的后罩和独立后盖。
- 底部左右喇叭采用真正穿孔网格，有孔壁和内部暗色挡板。
- 中间控制区嵌入前框，独立按键、指示灯、文字、前置 AV 接口与翻盖铰接边。
- 侧面和后盖真实散热开孔，后置 RCA、天线、电源接口及线缆护套。
- 后盖螺丝凹座、十字槽、铭牌；铭牌参数和编号为制作示意，不声称对应某个准确日立型号。
- 深灰 ABS 采用已有 4K SD 擦拭/细划痕数据；玻璃的微凹凸单独收弱。尺寸适配原场景位置，并非按实物测量校准。

## 验证与文件

完整正面、背面、控制区近景和原机位整景检查图位于 `04_renders/sq010/sh010/tv_reference/v001/`。模型含 117 个可编辑部件，零件数量本身不作为质量判据。

源工程 `02_assets/work/classroom_equipment.blend`，资产库 `02_assets/library/classroom_assets.blend`。接回使用最新磁盘工程，保留所有非电视对象的几何、材质绑定与位置，合并前后进行了哈希检查。

工作中源工程窗口已关闭，所以采用后台合并，未重新连接正在打开的镜头。已打开的镜头需重新载入资产库才能显示此次更新。

恢复快照：`07_pipeline/cache/tv_reference/source_before_merge.blend` 和 `library_before_merge.blend`。完整元数据在 `00_admin/asset_manifest.json` 的 `tv_reference_rebuild` 条目中；最终外形和老化程度仍待用户视觉验收。

最终从正式资产库重新打开镜头，确认集合含 117 个新版部件。原灯光近景为 classroom_close.png；前框受强光照射显著变亮，整景灰白外观不能单独用于判断是否加载旧模型。对照中性灯光图查看材质本色。
