# 当前工程基线

**2026-10-06课桌整体材质与迁移：** 当前入口 `02_assets/work/school_desk.blend`，贴图 `02_assets/textures/generated/kokuyo_desk`。桌洞／挂钩／固定片与旧管架协调，脚套深色橡胶及有效法线；21张依赖的相对路径与内嵌哈希、独立重开、原几何UV／木材保护通过。SHA256 `139da734695fabd36589982f0824b8b3473608189e8076a200c23f5bdef586e8`；技术pass、艺术review，正式镜头未改。只保留工程与依赖贴图，旧缓存清理见[记录](../06_review/kokuyo_desk_20261006/report.md)。

**2026-10-04本机复核与上下文补齐：** 读取D-XIANYI-SHI的关键CG聊天，见[恢复记录](../06_review/context_recovery_20261004/report.md)。F:/00_Projects/CG正式镜头由Blender 5.2.2后台只读重开，保存帧1071、1001–1100/24fps、cam_sh010_main、World=Sun，相机/天空两个Action，25个共享课椅实例、26个旧课桌实例、外部blend库引用0。主镜头SHA256为 `983984e3a1ff53903dfe9e53d280332cd03c8396b99b72f7420405db32afe638`，读前后不变。5张testgeometry_tommy贴图及Arial Narrow仍缺失；本机缺少school_desk_parts.blend、approved_material_library.blend与140帧旧候选。开始时主镜头和PureRef已有未提交修改，本轮未写工程；历史参数和“保留本机”不能覆盖本次设备实况。总PM刷新受40条历史证据缺失阻塞，制作验收状态不变。

**2026-10-03云端整理：** 用户授权当前镜头及实际依赖通过 Git LFS 上传，未引用资产仅排除上传、保留本机。缓存/旧候选/自动备份删除524个文件（约52.52GiB），最新源与可复现流程迁移72项并核对SHA256。课椅新入口 `02_assets/work/school_chair.blend`；最新课桌 `02_assets/work/school_desk_parts.blend` 和共享材质源 `02_assets/work/approved_material_library.blend` 尚未并入镜头，保留本机不上传。本轮主镜头仍为1001–1100/24fps、cam_sh010_main；5张既有opdef图像未解析，Arial Narrow为外部系统字体。镜头路径规范化结果与哈希以[本轮验证](../06_review/cloud_assets_20261003/report.md)为准；下方旧哈希是历史版本。140帧 `pose_fit_candidate.blend` 在清理开始前已缺失，历史重开记录不能证明它当前仍存在。

场景参数详细快照：2026-09-20；文件依赖复核：2026-09-29。这里记录源工程和最近可验证状态；任务进度看任务卡。修改工程前重新读取，本文不能覆盖用户后续保存。

**最新基线（2026-09-29）：** 固定主镜头已迁移为可直接编辑的本地工程，SHA256=`25fef6ac014f853ef93994e3ec9d0faa59dc35d63d4ccdb717ce6e3297ac116f`。重开实测为第1076帧、24fps、1001–1100，保留相机与天空两个Action；黑板 `Unique wiped writing surface` 可在镜头内直接选中，材质入口为 `LOOKDEV / material selectors`。其余263个集合实例保持变换。当前工程不再引用旧建筑/道具 `.blend`；旧源仍保留。迁移前恢复副本、画面对比与使用方式见[迁移记录](../06_review/classroom_pipeline_migration_20260929/report.md)。5张原有 `opdef:/Sop/testgeometry_tommy` 图像仍未解析，测试人物会呈紫色；正式灯光合成前须处理。140帧目标不变，本次迁移没有延长用户当前1001–1100帧范围。

2026-09-27清理保留了正式源、材质/贴图、原片、当前140帧候选，以及用户9月26日的新渲染 [sh010_v1.png](../04_renders/sq010/sh010/Scene/sh010_v1.png)。旧缓存、备份和测试版本已删除，见[清理记录](../06_review/cleanup_20260927/report.md)。正式主镜头当前仍为1001单帧、30fps、无Action；其SHA256已更新为 `0be2283f5645bc2b88386464ba07afdc225d5d4d7bd6e99856b9271edf1125c5`。下方9月20日光色参数和视频是历史快照，不能覆盖其后的手工保存。

## 固定工程

**2026-10-01最新共享实例修订：** 25把课椅现引用同一 `CHAIR / Shared editable asset`，只有29个母网格／31个根材质；母资产可在 `Chair_Asset_Edit` Scene直接编辑并同步所有实例。新增 `Seed Wear` 改变金属损伤位置／长短／覆盖，`Seed Grain` 改变木纹工艺裁切与轻微色差，其余表现Seed保留。网格与根材质份数减少96%，不等同于总RAM／显存减少96%。本轮读取用户前版发布后的最新保存，保留实际cam_sh010_main、1076帧、1001–1100／24fps、原世界／动作及其它资产；未恢复此前cam_corridor选择。候选／正式文件独立重开各215项与实际三点光／教室渲染通过，已原位保存，正式SHA256=`e4de73fe77439e24af2c91cfa9af7fc950147715603e7eca9e73faa420be0ea7`。下条独立网格方案是前版记录，当前编辑入口见[共享实例说明](../docs/workflows/edit_instanced_chairs.md)、[验证与评审](../06_review/chair_instances_20261001/report.md)。视觉待用户审阅。

**2026-10-01正式场景更新：** 用户通过整椅工作流后，已将25把旧集合实例替换为每把29个可直接编辑的实际分件，共725个独立网格／775个独立根材质。原控制对象摆位保留；木材、脏渍、金属、脚套表现Seed逐椅有稳定轻微差异，可在原椅子Empty的自定义属性中调整。工艺共用，模型与单椅参数可独立修改。正式文件独立重开839项检查通过，保留cam_corridor、1076帧、1001–1100／24fps、原灯光／世界、动作与其它资产。当前SHA256=`e2b09a1dbbded31773d2205300f1fbb7267feab67ca466b632c31822ab6cf939`；上方9月29日哈希是此前基线。[发布与渲染记录](../06_review/chair_scene_replace_20261001/report.md)、[编辑说明](../docs/workflows/edit_scene_chair_variants.md)。场景替换视觉待审阅，独立整椅材质已获用户通过。

| 职责 | 路径与链路 |
|---|---|
| 总镜头 | `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend` |
| 初始 Layout | 同目录 `drop_sq010_sh010_layout.blend`，保留作构图历史；不重跑覆盖当前摆位 |
| 建筑制作来源 | `02_assets/work/classroom_environment.blend`；2026-09-29前直接 Link，总镜头现已本地化 |
| 道具制作来源 | `02_assets/work/classroom_props.blend`；与发布库是独立版本，非当前镜头的实时编辑入口 |
| 旧道具发布库 | `02_assets/library/classroom_assets.blend`；2026-09-29前为链接来源，总镜头现已本地化 |
| 布料可重算源 | `02_assets/work/classroom_curtain_simulation.blend` |

## 2026-09-20重开实测

场景 `sq010_sh010`，主相机 `cam_sh010_main`，24 mm。当前正式文件只有 1001 单帧、30 fps、无 Action、无刚体世界；275 个本地对象，贴图缺失为 0。渲染设为 Cycles、2560×1080、1024 samples。

世界只有 Sky Texture / Background / World Output 三节点，启用 Sun Disc；日光角度约 17°/230°，无独立灯光。AgX / Medium High Contrast，曝光 −0.75 EV，白平衡 5000 K / Tint 10。角度是用户最新保存值，不恢复旧文档的 16.5°/250°。

证据：[scene_audit.json](../06_review/production_audit_20260920/scene_audit.json)、[当前主机位 32 spp 评审](../06_review/production_audit_20260920/current_main.png)。原文件 SHA256 `ddeedba12eb26c17587c9792bc9de124b3ded701c91e67d7cbd49982c33c3268`；这只是本轮快照。

用户已确认动态目标 140 帧，24 fps、制作 1001–1140；应先写候选再通过阶段检查发布，不直接把本段目标当成当前正式工程已经实现。

## 动态候选

当前审阅版本为 [坐姿修正版140帧灰模预览](../06_review/sh010_blocking_20260920/pose_fit_blocking.mp4)，可编辑候选为 `07_pipeline/cache/sh010_blocking_20260920/pose_fit_candidate.blend`。1280×540、24fps、5.833秒，140张独立帧和完整解码通过；[验证记录](../06_review/sh010_blocking_20260920/pose_fit_video_validation.json)。相机横移和身体段控制已建立，Root固定，人物采用修正后的静态坐姿，末段局部表演尚未制作。首帧提前显露的手脚已改善，但头部轮廓、家具视差及精确揭示时机仍有差距。

旧版灰模视频、旧候选工程和两套中间PNG序列已于2026-09-27清理。保留[三方对照](../06_review/sh010_blocking_20260920/comparison_pose_fit.jpg)及[首中末彩色对照](../06_review/sh010_blocking_20260920/comparison_beauty.jpg)作为精简证据；彩色图仍使用旧姿态，仅用于诊断材质与光色。最新候选、视频和首中末帧保留，正式镜头未替换。当前仍待Blocking方向评审，以[当前任务](../.scratch/sh010-test/issues/02-camera-blocking.md)为准。

## 最近资产修改与保护项

- 2026-10-01：整椅木材、金属、胶脚工艺／表现工作流已获用户确认，替换到正式教室文件；最新状态见上方10月1日正式场景更新。下面各独立资产条目的“待评审”保留为当时记录。

- 2026-10-01胶脚表现可见度修订（当前）：用户退回前版表现过轻，已修订SD老化／擦伤／划痕／灰污覆盖与尺度，增强斑驳黄化、泛白擦伤和底边灰污。原生SD66节点／18张4K输出；Age=0.75、Wear=0.75、Scratches=0.70，四件Dirt=0.65／0.60／0.70／0.63。保留原胶脚工艺组及几何UV法线、其它材质和捕获的用户未保存修改，同一独立课椅文件原位保存；实际归零差1、SD归零差0，独立重开56项通过。当前视觉待评审。[最新同光前后与报告](../06_review/chair_foot_cap_visibility_20261001/report.md)。

- 2026-10-01胶脚材质（前版，因表现不可辨认被退回）：独立课椅文件 `02_assets/work/school_chair.blend` 已应用四个浅黄哑光胶脚的工艺／表现两层，温和黄化、擦伤、细划痕与底边灰污独立控制。原生SD65节点／18张4K输出，Blender实际使用9张打包图；Metallic=0，本地绑定，保留几何UV法线及其它材质。SD归零差0、Blender归零最大差1，原位保存并独立重开55项通过。分件已获用户确认；材质视觉待确认。[最新材质报告](../06_review/chair_foot_cap_materials_20261001/report.md)。

- 2026-10-01胶脚分件（当前）：同一独立课椅文件中，将原连在LP_part_01／LP_part_13的三个胶脚沿现有16边界分离；加原LP_part_00共四个独立对象，归入CHAIR / Foot caps，四件材质可分别编辑并复用原黄白哑光胶脚外观。没有重生成。坐标／两套UV变化0，自定义法线转移后最大重新编码夹角约0.02021°；其它材质／木材／用户未保存编辑保留。已原位保存，独立重开30项通过。[分件报告](../06_review/chair_foot_caps_20261001/report.md)、[完整参考制作与逐级返修流程](../docs/workflows/reference_to_material_asset.md)。技术完成，视觉待确认。

- 2026-10-01金属颜色回归原参考（当前）：用户认为上一轮整面褐色过重。已在同一独立课椅文件恢复中性灰白旧漆，保留局部褐色锈蚀／掉漆，11件参数为Age=0.80、Age Color=#96988F、Age Coverage=0.30、Age Variation=0.40。木材、干净工艺、原损伤节点、几何UV法线和灯光机位保持；原位保存并独立重开54项及11件参数检查通过。最新图见[回归参考报告](../06_review/chair_metal_reference_color_20261001/report.md)，视觉待用户确认。下条整面灰褐版已被退回。

- 2026-10-01金属颜色修订：当前独立课椅文件已将11个涂漆部件从偏白调整为整面灰褐老化。表现组新增Age Color／Age Coverage／Age Variation，颜色#796957、覆盖0.78、局部变化0.30、漆面Age=0.95；木材、干净工艺组、几何UV法线和灯光机位保持。原位保存并独立重开通过原54项保护／依赖检查及新参数接线检查；原生SD和贴图未改。最新图见[调色报告](../06_review/chair_metal_age_color_20261001/report.md)，视觉待用户评审。

- 2026-10-01椅子金属材质：当前独立课椅工作文件 `02_assets/work/school_chair.blend` 已应用钢基底／灰白涂漆工艺和掉漆／锈蚀／老化／划痕／脏渍表现，覆盖11个漆面件与12个深色螺钉。原生SD77节点、21张4K输出；显式三向映射锁在部件本地，保留木材、原网格／UV／法线及胶脚。候选与当前文件重开54项通过；Blender归零最大差1个8位值，SD六个通道归零差全0。已原位保存，正式教室镜头未更新。视觉待评审：[金属制作报告](../06_review/chair_metal_layers_20261001/report.md)。

- 2026-10-01独立木椅材质候选：按用户要求在当前实时工程中彻底删除背面印记节点／Rear接口／reference_rear属性／StampMask打包资源。保留用户未保存编辑、几何／全部UV／法线、工艺／脏渍／侧壁及场景设置，原位保存 `02_assets/work/school_chair.blend`。重开无残留；同光背面渲染最大差1个8位值。正式教室镜头未修改，见[清理记录](../06_review/wood_stamp_cleanup_20261001/report.md)。

- 2026-09-28密封装配修正：删除30个REF rubber sash stop占位块；84块同类窗玻璃、336条胶条改为槽内U形结构，修复斜视宽黑边。玻璃嵌框、窗扇内槽和两侧压条同步调整，开度及五金控制器保持。建筑源已保存并重开验证，主镜头1094帧/24fps、1001–1100、本地动画保持且链接已刷新。[前后对比与实物资料](../06_review/window_glazing/index.html)、[当前发布哈希](../06_review/window_glazing/published.json)。

- 2026-09-28后续：按用户确认将外窗模板推广到所有同类教室/走廊推拉窗；当前可见36组窗锁、72处拉手统一，删除84个外沿排水槽凸块。原窗尺寸、开闭位置及相机/天空动画保留；正式源已保存，当前主镜头1094帧/24fps已刷新链接。[推广记录与最新哈希](../06_review/window_propagation/report.md)。下方PBR源哈希是推广前版本。

- 2026-09-28：外窗五金完成UV/PBR返工，覆盖六组窗锁与十二处拉手的78个金属部件；高低模源 `02_assets/work/window_hardware_authoring.blend`，共享4K贴图 `02_assets/textures/window_hardware/`。正式建筑源SHA256=`3b078a357644b8a02c8c5c27f5f11041cc2c03e395531d5a9ba7b34d270b81a5`，重开通过。保留用户最新开窗Y=-0.341201m、锁Y=270°；主镜头磁盘实测1089帧、24fps、1001–1100及相机/天空两个Action，链接与贴图有效。技术通过、视觉待评审：[最新五金记录](../06_review/window_hardware_pbr/report.md)。下条开度属于更早版本。

- 2026-09-27：左侧外窗六组月牙锁与十二处拉手按硬表面流程修正；侧装锁杯/拨柄联动、外轨扣座与真实布尔凹槽完成。`ctrl_window_left_04`保留Y≈−0.217078m，对应`ctrl_window_lock_02`的Y旋转180°解锁。建筑源已保存，总镜头链接已刷新；用户当前1001–1100/24fps、相机与天空Action保留，正式总镜头未强制保存。技术通过、视觉待评审：[五金修正](../06_review/window_hardware_correction/report.md)。

- 2026-09-27：用户在建筑源继续手工编辑后，为当前选中的 `WIN clear 5mm glass.006` 创建 `ctrl_window_left_04` Empty；20个活动窗扇部件保持世界位置并绑定，控制器仅开放Y平移。已保存、重开验证，用户未保存修改纳入恢复副本与正式源。详见[窗扇控制器](../06_review/window_controller/report.md)。仅做控制器，未新增风动。
- 保留最前一间完整教室。走廊 42 m，其他三间只留浅门窗立面和遮光，旧完整房间在禁用 Archive。长宽是制作设定。参考：[reference_upgrade](../06_review/reference_upgrade/report.md)。
- 四片窗帘已真实 Cloth 求解 1–120 帧，建筑源使用第120帧稳定形；未交付风动画，预滚收拢不能作为镜头动作。[cloth_tone](../06_review/cloth_tone/report.md)。
- 教室侧 12 块上亮窗与门上1块面板均为5 mm透明玻璃；旧 `REF blue upper infill*` 名称不代表不透明材质。[transom_glass](../06_review/transom_glass/report.md)。
- 黑板书写面采用 `Blackboard / Aged baked green coating`，只绑定 `Unique wiped writing surface` 和 `Board steel writing substrate`；旧材质作恢复数据。[blackboard_age](../06_review/blackboard_age/report.md)。擦痕与冷暖尚需随当前镜头评审。
- 后墙已实体围合，以材质方向性切面支持外侧主相机；不再添加旧 `lgt_rear_wall_blocker`。实例偏移、桌椅摆位和共用资产链接均需保护。[rear_classroom](../06_review/rear_classroom/report.md)。
- 铁盒角色为167个本地集合实例，当前为静态坐姿，无骨架。已恢复13身体段的归属，供后续局部动作；不得整体平移坐姿伪装行走。[角色审计](../06_review/production_audit_20260920/character/report.md)。

## 参考动作的最新结论

原片主全景是 REF027，源帧3823–3963（Out不含），140帧。人物逐渐露出主要由相机横向移动造成；人物头脚与同一椅子相对位置基本不变。局部上身/手臂变化可见，未验证步态或额外 roll。

以 [hero_motion_guide](../06_review/production_audit_20260920/hero_motion_guide.md) 覆盖初次审计中“角色走入/可能roll”的推测。全片 [44个参考容器](../06_review/production_audit_20260920/full_film_shot_inventory.md) 连续覆盖0–6027帧；包含黑场和复合段，不是最终镜头数。本地原片没有音轨。
