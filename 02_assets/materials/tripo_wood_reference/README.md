# Tripo课椅参考木材

座板和靠背各有独立原生SD源与归档：`reference_wood_seat.sbs/.sbsar`、`reference_wood_back.sbs/.sbsar`。40项4K输出位于 `../../textures/generated/tripo_wood_reference/`。

基础木纹使用内置imagegen根据用户课椅照片生成的1254²图像，已保存到项目 [reference_veneer_base.png](../../textures/generated/tripo_wood_reference/reference_veneer_base.png)；SD在4K进行通道计算，不把放大输出当作4K原始细节。完整提示词见 [imagegen_prompt.txt](imagegen_prompt.txt)。原参考仅作视觉输入，没有直接投射照片到模型。

工艺层包含蜜色涂层、宽幅自然弧形生长纹、顺纹微孔高度与粗糙度；表现层用独立蒙版控制长划痕、细划痕、凹点、老化和窄边露木。靠背背面印记只近似残损轮廓，没有猜测难以辨认的品牌文字。木材Metallic=0；浅表AO白色，未乘入底色。

本轮输入为Tripo最新版三角化候选，木板对应 `LP_part_02`（座板）与 `LP_part_09`（靠背）。输出为 [tripo_wood_reference.blend](../../../07_pipeline/cache/tripo_wood_reference_20260930/tripo_wood_reference.blend)，材质内 `Group` 为工艺层、`Group.001` 为表现层，默认节点名称保留，说明放在Frame中。两块木板各有三个效果控制：Scratches=0.90、Age=0.22、Wear=0.75。

新增 `UV_WoodReference` 为木板0–1平面坐标，切线法线读取相同UV；既有 `UVMap`、`UV_Material`、顶点、三角化与导入自定义法线未改变。侧边单独使用层压截面材质。Metallic、Roughness、Normal与蒙版为Non-Color；BaseColor为sRGB。贴图已打包入工程。SD资源文件路径仍指向本项目，迁移后应重定位资源；SBSAR内含资源。

抛光高光以用户工作室实拍为依据：保持整体平整，采用约22微米完整孔隙高度范围；粗糙度按顺纹微孔和涂层变化，清漆Normal／Roughness明确连接。起伏不是毫米级坑洼。

贴图为木板空间的可编辑分层输入，未重新烘焙到旧 `UV_Material` 图集。使用完整Blender材质可直接渲染；导出给引擎前需要另做资产UV烘焙。脚本入口是 `07_pipeline/scripts/tripo_wood_reference_sd.py` 和 `tripo_wood_reference_blender.py`，验证记录见 [评审报告](../../../06_review/tripo_wood_reference_20260930/report.md)。
