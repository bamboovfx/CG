# 课桌材质研究 · ArtStation

更新：2026-09-09。结构、尺寸和磨损强度仍以 props_01 同一实物的四张照片为依据。

访问情况：成功读取下列作者页面的公开制作说明；Chrome 与备用浏览器的页面控制超时，直接图片页请求返回 HTTP 403。尚未取得并检查这些作品的大图。没有下载付费材质，没有把艺术家展示图作为课桌贴图。

## 已读的制作说明

### Tsvetelina Valkanova — Painted Metal / Smart Material

[作者作品页](https://tsvetelina-valkanova.artstation.com/projects/mN3JY)

作者说明：分别制作 Rust、Rough Metal、Paint 三类 Substance Designer 材质，再通过遮罩生成器和 Anchor Points 在 Painter 中组合。

本项目应用：分离磨损与氧化遮罩；裸钢保留金属反射，锈层采用高粗糙度和孔蚀，漆层保留独立反射变化。实现为自写图层计算与 Blender 节点组，并未复现作者的 Substance 工程。

### Andrea Riccardi — Painted Metal Material

[作者作品页](https://andreariccardi.artstation.com/projects/QzmB2B)

作者说明：Age 与 Worn 独立控制老化与磨损；支持曲率和额外遮罩定位。页面列有参考照片、PBR 通道和节点图。

本项目应用：氧化年龄使用独立场，擦碰区可露出较完整的金属，积灰另设遮罩。暂未查看作者的通道大图，不声称复现了具体参数。

### Malte Resenberger-Loosmann — Breakdown Rust Material

[作品页](https://www.artstation.com/artwork/WBYQZD) · [个人展示页](https://iammalte.artstation.com/projects/WBYQZD)

作者介绍其 Rust 文章，强调理解参考和金属、锈蚀过程。此处保留作后续高清视觉研究入口；尚未读到图中完整教程，不推断其图层顺序。

## 待看大图的同类资产

[Nicholas D'Alfonso — Call of Duty Black Ops 6 / School Desk](https://www.artstation.com/artwork/1NleAK)

作品名及作者已由其公开作品集确认；用户 Chrome 中已有此页。当前无法读取大图，暂不写未经验证的材质细节分析。

## 本次落地与后续检查

- 2K 遮罩：WearMask、RustMask、DirtMask；使用独立场与影响范围。
- PBR 通道分别描述颜色、粗糙度、金属性和高度，避免复制同一噪声。
- 共享组：NG_Desk_PaintedSteel_SurfaceControls。
- 参数：Paint Tint、Rust Tint、Paint/Rust/Dirt Roughness Offset、Microheight m；默认保持当前外观。
- 固定源工程：02_assets/work/school_desk.blend；材质已标记为 Asset，贴图使用相对路径。
- 来源、2K 图及哈希：02_assets/textures/authored/school_desk/texture_manifest.json。

板边胶合层仍偏规整，部分剥落轮廓仍有程序感，色调还需在参考相近照明下判断。当前是单资产评审稿，没有替换到整景。
