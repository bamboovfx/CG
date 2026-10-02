# 完成可核对的局部表演与动态稳定性

State: backlog
Status: ready-for-agent
Owner: unassigned
Type: task
Blocked by: [动态 Blocking](02-camera-blocking.md)
Updated: 2026-09-20

## What to build

在相机通过后补足原片可验证的头部/上身/手臂局部动作，检查罐体与桌椅接触，交付整段可播放结果及必要的模拟读回证据。

## Acceptance criteria

- [ ] 动作方向和节拍有对应参考帧；未证实部分不伪造为原片表演。
- [ ] 没有可见悬浮、穿桌、手臂跳变或依赖关系错误。
- [ ] 窗帘静态Cloth稳定形与需要的镜头动态明确区分；若增加风，预滚和缓存重开一致。
- [ ] 没有将下一镜落座动作提前合并；没有为本镜头强加全身自由刚体。
- [ ] 用户通过全长表演方向。

## Evidence

待交付。

## Next

从角色相对椅子的局部变化开始，先做最少必要控制。
