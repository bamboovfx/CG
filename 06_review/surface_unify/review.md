# 木材统一、讲台锈蚀与墙面起伏

2026-09-12。按本轮要求更新常用镜头与资产库，以下均为当前 Blender 灯光下的真实渲染。

整景（旧测试图已清理）

## 木材

黑板木框、粉笔槽、讲台台面和木封边、书架、木柜、椅面、木踢脚等统一使用课桌当前的木纹颜色与材质逻辑；复用原始 Poly Haven plywood 4K 扫描，物理周期 0.6 m。每块板件新增独立米制 UV，木纹沿长边排列，原有 UV 保留。地板改用同源木纹，保留每块拼花木条的方向和接缝。

磨损比课桌更轻，保留浅划痕和少量边缘露木，避免每块板件都出现明亮的完整白边。课桌源文件本轮未改动。

![黑板木框与粉笔槽](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/surface_unify/v001/board_after.png)

![书架与黑板木材](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/surface_unify/v001/wood_after.png)

## 讲台烤漆金属

正面及两侧大白板改为旧烤漆金属的表面表现：下沿与板边锈蚀、少量面内锈点、旧漆色差，以及匹配掉漆范围的粗糙度和微凹陷。保留大部分漆层。锈和完整漆层均按非金属表面着色，并非把整块漆面设为 Metallic=1。

同时把原先陷入侧板的木封边向外调整 2 mm，消除大面积交叠亮条。

![讲台修改前](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/front_quality/v001/podium_final.png)

![讲台修改后](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/surface_unify/v001/podium_refined.png)

## 墙面

教室与走廊的 15 块主要墙体增加非破坏细分和真实 Displace，强度 1.4 mm、Midlevel=0.5，即名义最大偏移 ±0.7 mm；再叠加细抹灰与砂粒法线。原抹灰材质颜色与既有贴图保留。微小起伏在斜光、近景和较暗区域更明显，明亮正面受光处仍相对柔和。

相同机位、相同灯光：

墙面修改前（旧测试图已清理）

![墙面修改后](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/surface_unify/v001/wall_refined.png)

## 检查与文件

检查通过：相机、263 个集合实例变换和日照参数保留；图片依赖有效；课桌参考文件哈希不变；3 块讲台漆面已替换；15 块墙体存在实际细分与位移。96 个木材对象包含少量共享参照对象，不以对象数量代表视觉精度。详见 [验证记录](D:/00_projects/10_CG/Shot_Test/06_review/surface_unify/validation.json)。

[常用镜头](D:/00_projects/10_CG/Shot_Test/03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend) · [资产库](D:/00_projects/10_CG/Shot_Test/02_assets/library/classroom_assets.blend) · [原片参考](D:/00_projects/10_CG/Shot_Test/01_preproduction/references/film/drop_user_reference_clear.png)

教学、设备、椅子、教室外壳和走廊源工程同步更新。恢复副本在 `07_pipeline/cache/surface_unify`；恢复镜头指向恢复资产库，可以还原本轮前的完整外观。此轮是材质与微表面调整，不代表原片复刻已完成。
