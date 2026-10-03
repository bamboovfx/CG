# 独立木材表现层

来源：用户提供的旧课椅参考与已认可的imagegen木纹工艺层。此目录只制作表现层，不替换原 `tripo_wood_reference` 工艺源。

`wood_appearance_seat.sbs` 和 `wood_appearance_back.sbs` 保留独立 Scratches、Age、Wear 控制；SBSAR可用Designer渲染。配方资源为数学蒙版，没有裁取参考照片像素。老化包含发暗、褪色、涂层损伤；磨损按Tripo木板真实投影凸包、接触位置和顺纹破损构造。

生成器：`07_pipeline/scripts/tripo_wood_appearance_sd.py`。技术图位于 `02_assets/textures/generated/tripo_wood_appearance/`，2K蒙版经SD输出4K。`Raw_*` 未乘强度，Blender读取这些图；其余输出已乘SD参数。归零检查见 `06_review/tripo_wood_appearance_20260930/sd_validation.json`。

Blender表现组与三层米制Bump由 `07_pipeline/scripts/tripo_wood_appearance_blender.py` 创建，保存独立候选；凹槽距离为120／220／100微米。最新可编辑入口、渲染和验证见 `06_review/tripo_wood_appearance_20260930/report.md`。
