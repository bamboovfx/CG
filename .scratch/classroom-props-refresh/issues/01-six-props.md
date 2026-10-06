# 依次完成并替换六类教室资产

State: in-progress
Status: ready-for-agent
Owner: Codex
Type: task
Blocked by: none
Updated: 2026-10-06

## Acceptance

- [ ] 课桌完成可编辑分件、工艺／表现材质与实例差异并替换场景。
- [ ] 讲桌完成可编辑分件、工艺／表现材质并替换场景。
- [ ] 讲台完成合理模型分件、工艺／表现材质并替换场景。
- [ ] 书架完成可编辑分件、工艺／表现材质并替换场景。
- [ ] 书本完成纸张／封皮／书脊／装订分件、材质和实例差异并替换场景。
- [ ] 柜子完成可编辑分件、工艺／表现材质并替换场景。
- [ ] 各类UV／映射、微反射、损伤位置经同光透视近景与真实场景验证，保持原摆位和其它资产。
- [ ] 共享母资产与集合实例、参数可编辑、稳定种子、打包依赖、保存／重开通过，原位发布记录完整。
- [ ] 用户通过六类资产场景视觉。

## Evidence

- [规格](../spec.md)、[参考制作与逐环节回退](../../../docs/workflows/reference_to_material_asset.md)、[共享实例课椅流程](../../../docs/workflows/edit_instanced_chairs.md)。

## Comments

- 2026-10-03：缓存清理保留最新v4课桌分件，迁至 `02_assets/work/school_desk_parts.blend`，原始FBX在 `02_assets/authoring/school_desk/school_desk_raw.fbx`；材质源迁至 `02_assets/work/approved_material_library.blend`。它们尚未采用到主镜头，暂不上传；旧课桌中间版本已删除，制作/检查脚本保留在 `07_pipeline/workflows/classroom_props_refresh_20261001/`。原验收状态不变。

- 2026-10-01：用户授权六类资产依次制作并替换。当前实时Blender打开正式镜头且干净；先盘点模型／材质／参考，再决定各类别的局部修复与复用。

- 2026-10-06课桌阶段回场景：用户接受材质后补桌洞两处局部倒角，25张学生课桌原摆位共享13个母网格，旧讲桌inst_teacher_table按用户要求移除。正式文件与课桌独立重开、21张依赖及实际机位／同光近景通过，发布和技术验收见03卡。课桌逐实例磨损种子未新增；六类资产及整体场景视觉验收保持未完成。
