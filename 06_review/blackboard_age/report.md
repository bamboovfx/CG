# 黑板材质重做 · 2026-09-19

黑板书写面按绿色烤漆钢板制作：上中部有长期擦拭磨亮、粉笔固着残留及交错板擦细线；下部约四分之一保留较新的深绿底漆。靠窗侧增加轻微、宽泛的褪色，细槽保留少量积灰。

日晒与使用年限没有原片测量资料，当前强度是制作设定。工艺依据与实物观察见[参考整理](../../01_preproduction/references/blackboard_age_20260919/references.md)。

| 检查内容 | 结果文件 |
|---|---|
| 同光照、同机位修改前 | [黑板近景](board_before.png) · [完整镜头](classroom_before.png) |
| 修改后 | [黑板近景](board_after.png) · [完整镜头](classroom_after.png) |
| 擦痕、粉末和表面细节 | [局部近景](detail_after.png) |
| 几何、UV与其他材质保护 | [候选检查](candidate_checks.json) |
| 正式源文件重开、镜头链接与贴图检查 | [发布记录](published.json) |

近景和完整镜头使用现有场景光照、Cycles / OptiX、64 samples；评审相机不保存到总镜头。模型、木框、其他道具材质、建筑、灯光和主相机保持。本次通过后台工作，不声称用户的 GUI 已刷新。

正式文件：`02_assets/work/classroom_props.blend` 与 `02_assets/library/classroom_assets.blend`。总镜头仍通过现有库链接读取，文件本身保持原字节。旧材质保留为可恢复数据块。

原生 Substance 源和可调参数见 `02_assets/materials/blackboard_age/README.md`；5 张 4096 × 2048 PBR 输出与来源哈希见 `02_assets/textures/generated/blackboard_age/manifest.json`。新材质使用其中的 BaseColor、Roughness、Normal，并单独读取 Abrasion 遮罩。Height / Metallic 一并导出供后续流程使用。

参考照片中，厂商示例仅用于观察。项目已有的 Good Free Photos 擦痕照片经 2026-09-19 核对为 CC0 / Public Domain，用于提取细部残留遮罩。照片细节经过高通去除宽泛亮度，并由原创使用分区控制，未作为整板直贴照片。

备份位于 `07_pipeline/cache/blackboard_age_20260919/inputs.json` 所列位置；恢复时将 `props_before.blend` 或 `library_before.blend` 复制回清单中的正式路径，使原相对贴图链接正确解析。发布状态表示已完成制作与视觉检查，不代表用户已经批准艺术效果。
