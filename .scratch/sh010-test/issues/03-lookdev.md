# 在动态主机位下校准材质与冷暖

State: backlog
Status: ready-for-agent
Owner: unassigned
Type: task
Blocked by: [动态 Blocking](02-camera-blocking.md)
Updated: 2026-09-20

## What to build

在已经通过的相机路径下，使暖教室、冷走廊和黑板/背墙具有原片的层次，交付首中末lookdev样帧与针对性细节对照。

## Acceptance criteria

- [ ] 同机位对比原片与修改前后，先解决明暗、轮廓和主体焦点。
- [ ] 黑板深绿底色、上部擦拭残留、下部较新分区自然；不烘入实时窗影。
- [ ] 上亮窗保持玻璃，窗锁、窗帘和走廊已有细节继续有效。
- [ ] 色彩空间和实际采样尺度检查通过，其他资产/用户改动未被覆盖。
- [ ] 用户通过主机位样帧。

## Evidence

待交付。

## Next

Blocking通过后，先处理彩色对照已暴露的三项：阴影过亮偏暖、黑板宽泛擦痕过于显眼、桌椅摆位/表面差异过于整齐。先分开验证照明、材质与摆位，不用单一全局滤镜同时掩盖它们。

## Comments

- 2026-09-29：用户以原片全景、当前Blender直出和AE调色图指出：右侧走廊应冷、暗，但窗外仍应能看到云。第1076帧已保存工程实测只有 `Sky Texture → Background(Strength 1) → World Output`，Sun Disc启用，Sun Elevation约18°、Rotation约234°；场景没有Light对象，曝光−0.75、AgX Medium High Contrast。这个World同时承担暖直射、环境填充和可见天空，是右侧照度与天空细节难以独立调整的主要管线耦合。建议先在候选的1076帧把暖直射Sun灯、低强度冷天空填充、可见云层背景分开；走廊室内灯保持关闭，检查几何遮光与玻璃透射。固定单帧方向后，检查1001/1076/1100帧，并把现有Sky Texture太阳动画同步到新直射光。此条为只读诊断，没有修改镜头工程，也不改变本卡的Blocking前置。
