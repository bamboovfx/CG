# 讲台、黑板、吊灯与桌面修订

2026-09-12。已写回常用镜头和资产库，等待用户视觉评审。以下全部是 Blender 实际场景渲染，特写使用同一套场景灯光，没有另加展示灯。

![当前整景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/scene_final.png)

## 本轮修改

- 讲台：台面改用已有的 Poly Haven 4K 木纹及粗糙度，补板材侧边胶层细缝、面板装配缝和沿边缘的小崩口。去掉第一轮不自然的圆点磨损和粗糙的灰泥感。
- 黑板：木框改为有凹槽、内侧台阶的型材截面；调整绿色涂层与哑光响应，保留原有擦拭残留。板擦补织带经纬、缝线、细纤维和积粉，圆角增加分段并平滑着色。
- 吊灯：增加顶板、短支架、紧固件和接线，连接原灯体与天花板。9 盏灯共 18 处安装板顶面与天花板底面接触。
- 桌面：恢复被压缩的木纹明暗变化，接入已有 4K 扫描粗糙度，降低清漆与镜面反射。原几何磨损保留。
- 日照：Multiple Scattering 的 Sun Intensity 从 6 降到 5；太阳方向、HDR、曝光和相机构图保留。

## 桌面前后

同一近景机位。材质调整为主要变化，日照强度同时略降。

![桌面修改前](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/desk_before.png)

![桌面修改后](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/desk_after.png)

## 教学部件与安装

![讲台近景](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/podium_final.png)

![黑板擦特写](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/eraser_final.png)

![吊灯与天花板连接](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/fixtures_after.png)

## 对照与限制

![原片参考](D:/00_projects/10_CG/Shot_Test/01_preproduction/references/film/drop_user_reference_clear.png)

本轮改善了局部结构和材质可读性，尚不代表完成原片复刻。整景右侧走廊仍偏亮，黑板绿色和明暗分布与参考有差异。极近特写中板擦主体纤维仍有程序化痕迹，桌面原有少数崩口也偏尖锐。微小纤维和板材接缝在整景中的可见性受像素覆盖限制。

完整渲染为 1920×810；特写按评审对象取景。验证通过：相机及 263 个集合实例的变换保留，外部图片路径有效，固定资产库引用有效，安装板与天花板高度误差小于 0.001 mm。详见 [检查记录](D:/00_projects/10_CG/Shot_Test/06_review/front_quality/validation.json)。

常用镜头：[drop_sq010_sh010_shot.blend](D:/00_projects/10_CG/Shot_Test/03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend)。同步更新教学、设备、课桌源工程和 [classroom_assets.blend](D:/00_projects/10_CG/Shot_Test/02_assets/library/classroom_assets.blend)。恢复副本位于 `07_pipeline/cache/front_quality`，未另建常用工程版本。
