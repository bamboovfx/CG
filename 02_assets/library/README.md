# 教室资产库

`classroom_assets.blend` 是唯一日常编辑的资产源；镜头工程通过 Collection Instance 链接它。单位为米，Z 向上。

## 编辑与复用

1. 摆位、灯光、相机、调色：打开 `../../03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend`。
2. 修改模型或共享材质：打开本目录 `classroom_assets.blend`，在 Outliner 选择对应 `AST_` 集合。隔离集合后编辑，直接保存此库；镜头重新打开或 Reload Library 后更新全部实例。
3. 跨项目复用：File > Link > 选择库 > Collection > 选择一个 `AST_` 集合。保留 Collection Instance，单独移动实例。也可用 Asset Browser 添加本目录为资产库。
4. 需要独立改形时另行建立 Library Override 或 Append；默认共享版本不复制几何。新项目应一起复制 `02_assets/library`、`02_assets/textures` 和 `02_assets/hdri`，保持相对结构。

集合 `instance_offset` 是放置原点；资产元数据包含原点、米制尺寸、面数与资产 ID。桌与椅分开封装，材质和贴图共享。镜头中的 `instance_id` 唯一。

## 贴图

- 实际连接的工作贴图为 2048×2048；HDR 为 2048×1024。
- 木板、地面、墙和织物使用已有 CC0 扫描素材；4K 源保留，木板/地面工作图在 `textures/authored/classroom/2k` 中另存 2K 衍生文件。
- 金属、漆面、橡胶、纸、玻璃等使用原创程序化 2K 微表面。它们不是扫描 PBR；微法线由高度扰动近似。扫描材质使用 OpenGL Normal Map，程序化三向微表面使用 Bump，避免圆管接缝。
- 公告及糖果标签为原创排版，不是原片文字转录。颜色图 sRGB，粗糙度/法线 Non-Color。
- 路径、许可、来源、尺寸和哈希：`../../00_admin/asset_manifest.json`、`texture_dependencies.json`、`asset_catalog.json`。

## 灯光与风格

镜头 World 的 `HDR Rotation` 控制旋转，`HDR Strength` 控制照明强度。HDR 来源为 Poly Haven 的 Kiara 1 Dawn，CC0；仍用独立太阳控制窗影。玻璃对阴影射线使用薄平板透射近似，不是折射焦散模拟。

Compositing 的 `Afternoon style - Mix 0 bypass` 节点提供 Hue、Saturation、Exposure、Mix。Mix=0 或 Mute 关闭。它实现色相、饱和度与曝光调整，不是严格的 HSL 色彩空间变换；AgX 保持为显示变换。

## 当前边界

已完成本轮静态资产结构与 2K 工作材质搭建，附有整景和 14 组近景。整体旧化、镜头级灯光和最终滤镜仍可按参考继续精修。人物 167 个罐体实例保留稳定 sim_id；刚体代理、碰撞间距、质量和约束尚未测试，不能把可独立实例化当成动力学通过。

日常只保存固定工程。旧构建脚本用于追溯首次迁移，不应直接覆盖已经手工修改的资产库。
