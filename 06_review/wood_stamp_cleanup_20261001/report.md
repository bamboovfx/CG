# 背面印记清理 — 2026-10-01

按用户要求，彻底删除印记相关数据。当前实时工程存在未保存编辑，先保存在恢复副本，再定向清理并原位保存；没有从旧磁盘版本恢复场景。

当前文件：[tripo_wood_side_back.blend](../../07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend)。恢复副本：[before_cleanup.blend](../../07_pipeline/cache/wood_stamp_cleanup_20261001/before_cleanup.blend)。

- 删除座板／靠背表现组内的印记贴图节点、三项专用运算、专用转接点、印记混合和旧关闭说明，以及两个材质根树中的Attribute，共16个节点。
- 删除两个Rear输入接口、两块木板的reference_rear面属性、两张打包StampMask及legacy_stamp_disabled属性；修正根树说明框文字。
- 原印记混合Factor已经为0，直接把其基础颜色输入接回原输出。共享Age、DirtColor、其它老化／磨损／划痕及独立表面脏渍继续保留。

实际工程重开验证无残留：[reopen_validation.json](reopen_validation.json)。清理前后木板几何、全部UV和法线、工艺／独立脏渍／侧壁节点摘要、所有对象世界位置、当前活动Plane与OBJECT模式、相机／世界／帧／渲染设置摘要相同，见[审计](validation.json)。

1200×900、48spp、固定背面机位和种子，保持当前世界／三点灯／色彩管理。同光前后最大差1个8位值，平均差0.00003935，大于2的差异为0，见[像素比较](render_comparison.json)。

![清理后背面](after.png)

清理已完成。整体材质仍沿用原任务的视觉评审状态。历史SD／扫描辅助制作源及旧阶段候选保持作为制作记录；本次未重跑历史初建脚本，也未修改教室正式镜头。
