# 喇叭积尘与灯架塑料 — 2026-09-16

已保存到 `02_assets/work/classroom_equipment.blend`，保留当前场景原有材质节点及用户编辑。未合入镜头或资产库。

- 原生 Substance Designer 图生成 2K DustMask / Grain；Blender 根据朝上法线和局部遮蔽分配积尘。
- 喇叭塑料、钢丝网和背板各有独立粉尘层。灰尘量 Value 节点位于 Settled dust 注释框，当前强度分别为 1.35、1.65、0.7；设为 0 可关闭。
- 灯架 15 个原 EQ SD enamel 部件复用 Speaker / SD worn plastic，包括框体、边板、灯座外壳和顶部安装板。灯管及金属紧固件保持原材质。
- 粉尘贴图使用 Object 坐标，20 cm 周期，Non-Color。细粉凹凸为着色效果，不新增几何。
- Cycles 完整与近景渲染检查：speaker.png、dust_detail.png、fixture.png、fixture_detail.png。
- 实际绑定对象、贴图尺寸见 validation.json。
