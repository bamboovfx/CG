# 讲台轻微锈蚀 · 2026-09-16

已保存到道具源 `02_assets/work/classroom_props.blend` 和发布库 `02_assets/library/classroom_assets.blend`。后台重新打开总镜头，确认 `inst_teacher_podium` 读取到新版材质；未改动镜头文件。

三个面板的锈蚀遮罩平均值由 8.3%–8.4% 减至 0.9%–1.2%。该值来自规则表面顶点采样，不是渲染画面的像素覆盖率。锈色改为低对比灰褐色，锈坑幅度由 0.28 mm 降为 0.06 mm，漆边起翘由 0.40 mm 降为 0.12 mm。保留原有 paint_stain、微表面、木材划痕与磨损。

使用相同相机、灯光、Cycles OptiX 48 samples 输出并检查完整讲台和底边近景。原先正面的大块深褐色腐蚀已消退，底边保留少量轻锈与掉漆；污渍和木面细节仍可见。物体、网格、材质分配、集合偏移及摆位检查通过。

![修改前](before_full.png)

![修改后](after_full.png)

![修改后底边近景](after_detail.png)

完整参数及发布验证见 `published.json`；恢复副本位于 `07_pipeline/cache/podium_subtle/props_before.blend` 和 `library_before.blend`。发布时 Blender 实时连接已断开，未执行 GUI Reload；重新打开总镜头可直接读取更新。如界面仍保留旧库数据，Reload `classroom_assets.blend`。
