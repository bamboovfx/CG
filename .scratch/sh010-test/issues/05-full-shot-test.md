# 输出完整灯光与合成测试

State: backlog
Status: ready-for-agent
Owner: unassigned
Type: task
Blocked by: [材质冷暖](03-lookdev.md), [局部表演](04-local-performance.md)
Updated: 2026-09-20

## What to build

从已通过的场景输出140帧连续序列，完成有明确色彩处理的合成和评审视频，以连续播放检查静帧看不到的问题。

## Acceptance criteria

- [ ] 先测首中末噪声和耗时，再选择整段渲染设置并记录依据。
- [ ] 序列无缺帧，视频24fps/140帧，图像与色彩处理明确。
- [ ] 首中末并列原片，完整播放检查闪烁、跳变、过曝和黑位。
- [ ] 无重复显示变换；降采样预览与最终交付清楚区分。
- [ ] 用户通过最终画面或明确列出需要返工的项目。

## Evidence

待交付。

## Next

两条前置都通过后执行全长测试。
