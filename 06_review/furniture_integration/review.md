# 桌椅整景替换 · 2026-09-11

按用户本次明确要求，将已细化课桌与椅子放入固定镜头，修正上一轮配套中课桌反向180°的问题。

## 方向与摆放

- 课桌源模型的学生开口在本地+Y。每个课桌实例在原布局角度上增加180°，让开口指向其配套椅子；椅子沿原角度面向教室+Y黑板方向。
- 正式镜头共24张新课桌、24把新椅子；旧桌椅实例全部替换，实例总数保持261。
- 桌椅共用约1.12313的等比倍率，保持管材与木板比例；桌面仍在原来的Z≈0.773m。源资产尺寸保持不变。
- 地板表面Z=0.0205m，家具以此落地。椅子相对桌中心后移约0.595m。
- 人物旁06号课桌向+X、−Y各移动75mm，以较窄的新桌面承接既有手部位置；人物、相机、灯光和其他实例变换未改。
- 新桌面比旧模型更窄，画面中的过道会略宽；这是新资产替换产生的尺度差异。

## 保存位置

- 固定镜头：`03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`
- 正式资产库：`02_assets/library/classroom_assets.blend`
- 库中新增 `AST_school_desk_HP`、`AST_school_chair_HP`、`AST_school_desk_chair_set_HP`，原库既有集合保留。
- 修正后的组合预览：`07_pipeline/cache/chair_highpoly/paired_preview.blend`。
- layout文件保留为原布局记录；本次工作写入shot文件。

## 图像检查

![整景](../../04_renders/sq010/sh010/furniture/v001/scene.png)

![学生侧桌肚开口与脚套](../../04_renders/sq010/sh010/furniture/v001/student_side.png)

![人物手部接触](../../04_renders/sq010/sh010/furniture/v001/hero_contact.png)

## 验证与恢复

- [逐组替换记录](integration.json)：保存原变换、当前变换和局部布局调整。
- [验证记录](validation.json)：依据桌肚卷边与封闭面标牌的实际几何位置核对方向，不只检查Euler角度；24组全部通过。
- 全部资产链接与外部图片路径有效；固定文件保存后再次打开验证。
- 本次替换前的库与镜头恢复点保存在 `07_pipeline/cache/furniture_integration/`，名称分别为 `classroom_assets_before_integration.blend` 和 `shot_before_integration.blend`。恢复时需复制回各自固定路径，使原有相对依赖正确解析。

本次完成资产入景与朝向修正，整景的构图、灯光和原片匹配质量仍是后续独立工作。
