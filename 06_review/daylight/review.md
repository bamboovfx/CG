# 教室原生 Daylight + HDR 调光

2026-09-12。已写回正式镜头；本轮为按参考方向调整的灯光版本，待用户视觉验收。

![当前完整渲染](D:/00_projects/10_CG/Shot_Test/04_renders/sq010/sh010/daylight/v001/scene.png)

## 使用方式

World 数据块为 **Daylight + HDR**。在原生 **Sky Texture** 中调整 **Sun Elevation**（太阳高度）和 **Sun Rotation**（太阳方位）；Multiple Scattering 会随太阳高度改变天空和阳光颜色。Sun Disc 已开启，原来的独立 Sun 已停用，避免叠加第二套日照。

Sky Texture 当前值：高度 **9.3°**、方位 **228°**、Sun Intensity **5**、Air **0.8**、Aerosol **0.6**。Sun Intensity 在同日的教学部件与桌面修订中从 6 降为 5，其余上述参数保留。这些是本镜头的制作参数。

**Daylight balance** 节点组集中控制亮度：

| 参数 | 当前值 | 用途 |
|---|---:|---|
| Sky strength | 0.025 | 室内的天空和日照整体强度 |
| HDR strength | 0.05 | HDR 分支强度 |
| HDR blend | 0.06 | HDR 着色器混合量；0 为纯程序天空 |
| Exterior strength | 0.70 | 直接看到或透过玻璃看到的窗外亮度 |

HDR 使用已有的 Joburg Central Sunset 4K EXR，Mapping Z 为 **176.3°**。城市和云层细节只作少量补充；6% 是节点混合量，不等于实际照度占比。

窗外曝光分支的 **Mix=0** 可关闭单独增亮。它保留室内照明和反射使用的原始环境强度。节点均保留默认名称，解释放在独立注释框中，没有常驻脚本或自定义驱动依赖。

色彩管理为 AgX / Medium High Contrast，原曝光 0.65 与已有合成调色组保留。

## 对照与检查

![用户提供的原片参考](D:/00_projects/10_CG/Shot_Test/01_preproduction/references/film/drop_user_reference_clear.png)

本轮重点是低角度窗影、明亮窗外、室内明暗差和暖色受光面。当前右侧走廊仍比参考偏亮，整景构图和材质色彩也未在本轮全面重做，不能视为完成原片复刻。

已检查 1920×810 完整渲染、相机与物件布局、贴图路径。正式保存前 Blender 进程退出，因此从本轮已保存的现场快照与检查过的候选工程离线写回；此前磁盘文件已留恢复副本。

另从正式文件重新打开，以太阳高度 5° 做过整景小图验证：窗影随角度变化，天空和阳光自然转暖。该测试没有写回正式工程，正式太阳高度仍为 9.3°。

正式文件：[drop_sq010_sh010_shot.blend](D:/00_projects/10_CG/Shot_Test/03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend)
