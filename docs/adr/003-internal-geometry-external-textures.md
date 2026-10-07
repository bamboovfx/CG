# ADR 003：镜头内模型与外部贴图

日期：2026-10-07。状态：采用，候选与正式重开及同帧对照技术通过，已原位发布；见[验收](../../06_review/shot_internal_geometry_20261007/report.md)与[任务卡](../../.scratch/shot-external-links/issues/02-internalize-geometry.md)。替代[ADR002](002-external-geometry-local-shading.md)。

用户在外部依赖迁移后明确“模型不要放到外部，就放到内部就行”。超出2GiB的主要原因是2.114GiB内嵌图片，模型数据约60MiB；解除Git LFS单文件超限无需让模型外链。

固定镜头 `03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend` 保存全部当前模型、UV与属性，以及原本地材质、节点组、对象和实例。模型与shading都在镜头内部编辑，保留当前OBJECT材质槽绑定。贴图继续使用项目内相对路径，不重新打包。旧 `classroom_geometry.blend` 保留为历史迁移资料，当前镜头不依赖它。

代价是镜头包含约60MiB几何数据；收益是直接在镜头中修改模型。跨设备仍需下载贴图。以最新保存源为基线，在候选核对几何属性、共享引用、材质节点与有效绑定、相机世界与动作，实际修改并恢复网格和shader参数，独立重开及同帧画面对照后原位发布。此技术迁移不替代镜头艺术验收。
