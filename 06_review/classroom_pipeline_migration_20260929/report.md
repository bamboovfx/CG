# 教室材质编辑管线迁移（2026-09-29）

## 结果

固定镜头工程 [drop_sq010_sh010_shot.blend](../../03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend) 已发布为本地可编辑版本。黑板、窗框和其他材质能在镜头的相机与灯光下直接调整。旧建筑、道具及发布库文件仍保留，但不再自动驱动这个镜头。迁移仅改变编辑关系，没有有意改变构图、材质外观或动画。

用户选择：同一教室的后续镜头默认共用材质，特定镜头需要不同外观时另设镜头例外。目前工程只有 `sq010_sh010` 场景；第二个场景的共享与隔离关系已在临时测试中验证，尚未创建正式第二镜头。

## 在 Blender 中编辑

1. 打开固定镜头工程，保持相机视图。需要看最终 Sky Texture 和灯光时，切换到 **Rendered** 视图着色；材质预览模式使用自己的预览环境，不能作为最终灯光判断。
2. 改黑板：在 Outliner 搜索 `Unique wiped writing surface`，选中它。进入 **Shading** 工作区或将一个区域设为 **Shader Editor**；编辑 `Blackboard / Aged baked green coating`。黑板书写面在场景中是真实对象，不再需要打开旧发布库。
3. 改窗框、玻璃及其他被集合实例包住的共用材质：展开顶层 `LOOKDEV / material selectors`，搜索 `MAT / ` 加材质名，选中对应入口，在 Shader Editor 改节点。入口对象与场景物件指向同一个材质数据块；这些选择片不参与渲染并位于镜头外。改完用目标机位渲染一帧确认。
4. 常规修改直接作用于这个教室的共用外观。后续某一镜头要特殊调色时，不要直接改该共用材质：先复制该镜头需要变化的对象/网格与材质，并在另一场景绑定例外，检查原镜头没有跟着改变。

旧 `classroom_props.blend` 与 `classroom_assets.blend` 是不同副本。迁移采用**当前镜头实际看到的发布库材质**；黑板书写面依然是原镜头的16节点材质，而不是道具制作源的另一套19节点材质。改旧源不再刷新当前镜头。

## 验证与范围

- 输入：2026-09-29 09:54 已保存的正式镜头，SHA256 `9312d03a0b5b183a568fc935b0938dee1467d5596bee1e19ce5af27a48602b0e`。输出正式镜头 SHA256 `25fef6ac014f853ef93994e3ec9d0faa59dc35d63d4ccdb717ce6e3297ac116f`。
- 重开确认：第1076帧、24fps、1001–1100；`cam_sh010_mainAction` 与 `Golden afternoon studyAction` 保留；263个其余集合实例及其变换保留。黑板原实例改为可直接选中的1252个场景对象，材质选择入口247个。本地化后无外部 `.blend` 库依赖。详见[重开验证](../../07_pipeline/cache/classroom_pipeline_migration_20260929/published_validation.json)。
- [迁移前画面](before.png)与[迁移后画面](after.png)：同一相机、第1076帧、960×405、Cycles OptiX 32 samples、固定seed 23；RGB绝对差均值0.00351/255、最大6/255，99%通道值完全相同。差异图见 [8倍放大](diff_x8.png)。画面和几何位置保持一致。
- 临时第二场景检查：材质数据块共享；相机和 World 数据块独立；黑板单对象/网格/材质的例外不会改动原黑板，其余1251个黑板对象继续共享。临时测试未写入正式工程。
- 这是编辑管线交付，不是镜头成片。用户确认的140帧目标仍待制作，当前工作工程的1001–1100帧段未被迁移改写。

五张原有 `opdef:/Sop/testgeometry_tommy` 图片仍未解析，导致测试人物在画面中呈紫色。迁移前后都如此；进入正式 Lighting/Comp 前应恢复贴图或替换这个测试资产。

## 恢复与文件职责

- [迁移前可重开副本](source_before.blend)：原分文件链接状态，已验证能解析两份旧 `.blend` 依赖。恢复时应先备份当前正式工程并确认没有更新工作需要保留。
- `07_pipeline/cache/classroom_pipeline_migration_20260929/candidate.blend`：迁移候选；`candidate.json`、`validation.json`、`published.json` 保留结构和哈希记录。候选不应作为日常编辑入口。
- `02_assets/work/classroom_environment.blend`、`02_assets/work/classroom_props.blend`、`02_assets/library/classroom_assets.blend`：保留历史与独立资产制作内容，不删除。后续若需要从这些来源引入改动，先在候选中选择性合并，再检查镜头画面，不整库覆盖当前工作。

设计取舍与实测见[管线评审](../pipeline_review_20260929/proposal.md)。
