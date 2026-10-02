# 教室后墙与走廊修正 · 2026-09-17

已通过后台 Blender CLI 更新并覆盖固定建筑源和总镜头。重开总镜头检查通过，贴图/链接库无缺失；主相机变换、焦距、灯光变换、能量与颜色和修改前一致。

## 本次完成

- 建筑源新增 `AST_classroom_rear`，总镜头新增对应直接 Link 实例。包含实体后墙、墙裙、踢脚线、顶角线、展示板、30 格低柜、标签框、螺钉、图钉、纸张厚度和轻微翘曲。
- 展示区按参考的五排竖排书法与左侧通知区构成重建，书法为新制作图集；用字体生成的内容是制作替代，未声称逐张还原原片笔迹。
- 柜体约 7.19 m 宽、0.45 m 深、0.94 m 高；每格约 45.5 cm 宽。保留材质族的 2K 微表面，书法图集为 4092 × 4095。
- 总镜头走廊实例 Y 从 0.21554 m 回到源坐标 0。隐藏源文件里进入前墙内侧约 10 mm 的冗余邻室隔墙，以及两处完全重合隔墙；原对象保留作恢复。
- 后排桌椅按排前移；糖果罐角色与第 06 组桌椅一起移动 1.0875 m，保持相对关系。局部左右间距仅修正不足的区域；桌椅尺度和朝向不变。

## 比例与检查

| 项目 | 求值后结果 |
|---|---:|
| 教室内宽 × 深 | 8.00 × 10.45 m |
| 地面至天花净高 | 约 3.55 m |
| 柜前至最近后排椅子的净宽 | 0.950 m |
| 相邻桌子之间最小横向净宽 | 0.575 m |
| 走廊进入室内核心区域的网格 | 0 |
| 缺失图片 / 库依赖 | 0 |

![实际平面](D:/00_projects/10_CG/Shot_Test/06_review/rear_classroom/clearance_plan.svg)

尺寸是本场景的制作设定。参考[府中市学校设施资料第 2 页](https://www.city.fuchu.tokyo.jp/gyosei/kekaku/kyogikai/koukyoushisetu/gakkousiseturoukyuukataisaku/H29-30gakousiseturoukyukataisaku/kaisaikekka.files/26.pdf)：该市方案给出中学 8 × 10 m 的墙芯尺度、550 mm 通路参考值及 460 mm 储物宽度。这里用于校核量级，不将其当成所有日本学校的统一标准；也没有把当前 950 mm 后通道当作该方案 1500 mm 无障碍转向区。

实物构成另参考[越後屋スタジオ的真实旧校舍教室](https://www.echigoyastudio.jp/casestudy/studio/01561/)，原片截图仍是后墙构成的主要依据。当前预览沿用用户已保存的午后灯光；蓝暗参考截图的曝光和调色没有直接复制。

## 相机剔除

主相机仍在 Y=-7.5 的后墙外。新后墙组件使用 `Rear architecture directional camera cutaway` 材质组：只有朝向来自 -Y 外侧的 Camera Ray 透明；Shadow、Diffuse、Glossy 保留原表面。从室内的反拍相机看，后墙与柜体正常显示。节点保留默认名称，说明在注释框里。

原先单独的 `lgt_rear_wall_blocker` 在用户本次保存文件中已不存在，由完整后墙承担围合。用户新增 `Cube` 的变换原样保留（X≈24.26 m，位于教室外），仅关闭 Camera 可见性，不用它代替后墙。普通遮光立方体可在 Object Properties → Visibility → Ray Visibility 关闭 Camera，保持 Shadow 开启；不要关闭整个物体的渲染开关。

## 文件与恢复

- 建筑源：`02_assets/work/classroom_environment.blend`
- 常用总镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 总镜头活动相机仍是 `cam_sh010_main`；新增 `cam_sh010_rear_review` 和 `cam_sh010_rear_detail` 可切换查看后墙。
- 修改前原始字节备份：`07_pipeline/cache/rear_classroom_20260917/before_rear_classroom_environment.blend` 和 `before_rear_drop_sq010_sh010_shot.blend`。
- 核验数据：`published_validation.json`；变更记录：`build_manifest.json`；发布哈希：`publication.json`。
- 正面、后墙、纸张近景均完成 Cycles / OptiX 96 samples 渲染，并检查相机剖切与材质显示。当前结果是已补全的静态后墙场景，不代表整个短片外观已逐像素匹配或动画已完成。

## 画面对照

用户原片参考（保留原图，未调亮或改色）：

![原片后墙](D:/00_projects/10_CG/Shot_Test/01_preproduction/references/film/drop_rear_user_20260917.png)

完成的后墙：

![后墙](D:/00_projects/10_CG/Shot_Test/06_review/rear_classroom/04_rear_final.png)

主镜头检查：

![主镜头](D:/00_projects/10_CG/Shot_Test/06_review/rear_classroom/05_front_final.png)
