# 玻璃嵌槽与密封条修正 · 2026-09-28

已保存固定建筑源 `02_assets/work/classroom_environment.blend`，并刷新当前主镜头链接。全体同类窗84块玻璃、336条胶条统一修正，删除30个 `REF rubber sash stop*` 占位块。历史隐藏Archive不修改。

## 原因与修正

右侧 `REF EPDM seal stile.019` 的原截面深36mm，左侧同类为41mm，而玻璃只有5mm厚。旧模型把胶条做成横跨窗扇厚度的黑色实心侧壁；玻璃又未嵌入框内，与压条存在间隙。此前推广保留了旧截面，正视检查没有暴露斜视的宽黑边问题。

本轮重新做窗扇的开口槽、包覆玻璃边缘的U形胶条和两侧金属压条，玻璃边缘嵌入槽内。胶条总厚8.4mm、玻璃嵌入6mm、外露唇口约1.2mm。这些是适配当前模型的CG尺寸，不声称复刻某一厂商型号或满足施工标准。胶条保留原深灰材质，没有靠染白消除黑边。

所有对象矩阵、父级、窗扇开闭位置与五金控制器保持；原有拉手凹槽布尔和烘焙五金材质保留。修正网格为封闭截面，配小倒角；玻璃保留5mm厚度。

## 检查

- [同机位前后对比与实物参考](index.html)：使用当前镜头1094帧光照，新建斜视评审相机；两张图同灯光、48 samples、1280×1000。评审相机未写回正式文件。
- [候选检查](validation.json)、[正式源重开检查](published_validation.json)：1428个目标分件修改；未发现非目标几何变化、对象位移、非流形网格或建筑源缺失贴图。
- [主镜头保护](shot_reload.json)：本地对象、相机、动作、当前帧及时间范围保留。主镜头保留当前编辑状态，不强制保存。
- [发布哈希](published.json)。恢复副本位于 `07_pipeline/cache/window_glazing/`。
- 两次评审渲染都记录了主镜头原有 `opdef:/Sop/testgeometry_tommy` 贴图路径警告，与本次窗户资产无关；未擅自修改该角色资产。建筑源自身贴图检查通过。

技术检查通过；当前视觉结果仍由用户评审。

## 实物与剖面依据

1. [玻璃供应商：胶条截面、包覆玻璃照片、安装步骤](https://www.giya-man.com/product/624/)：U形胶条先包玻璃边，再随玻璃装入铝框。下载了截面和实际手持安装照片。网页整窗图属于商品展示，不能据此精确量尺寸。
2. [窓工房：拆框、玻璃就位及完工照片](https://www.34al.com/eg/eg-spacia/caulking-st-akishima-a.html)：该例使用真空玻璃和现场密封胶，工艺与本模型胶条不同；只参考玻璃进入框槽、密封处在玻璃与框之间的装配关系。
3. [Glass Wonderland：板玻璃标准施工剖面，PDF第5页/印刷页164](https://glass-wonderland.jp/cms/wp-content/themes/httpdocs/assets/pdf/total_s13-160.pdf)：比较玻璃胶条、压条和其他垫片的剖面，区分槽内嵌入量与外露边。
4. [长崎サッシ工業：旧窗胶条更换记录](https://www.pattolixil-madohonpo.jp/shop/nagasaki/mh000466/photo/50862)：文字说明采用包玻璃的コ字形胶条。图片服务器拒绝下载，保留网页入口，没有伪称已查看其细节。

下载资料在 `01_preproduction/references/window_glazing_20260928/`；[来源/版权/哈希清单](../../01_preproduction/references/window_glazing_20260928/manifest.json)。仅限本地参考，未取得再分发许可。
