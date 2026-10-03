# 椅子金属分层材质

原生Designer源：`chair_metal_layers.sbs`，编译包：`chair_metal_layers.sbsar`。77个原生节点、21张4K输出。参考为用户旧课椅照片；照片只观察，不作为贴图采样。

工艺层输出灰白涂漆Color／Roughness／Metallic／Height／OpenGL Normal／AO。表现内容输出ChipField、RustColor／Roughness／Height、AgeMask、ScratchMask和DirtMask；SD内的Final_*为通用分层样片，Preview_*为样片蒙版。Blender使用独立的资产位置包络，最终效果以实际椅子渲染为准，SD样片不替代资产掉漆位置。

Blender分为工艺组与表现组。11个漆管／连接板和12个深色螺钉分别绑定，深色螺钉使用工艺组变体。各表现节点公开Wear／Rust／Age／Scratches／Dirt，全部归零恢复工艺。Rust受掉漆位置限制；完好漆与锈为非金属，露钢区为金属，滤波和强度混合处为过渡值。

内容覆盖12cm；每部件本地坐标还原原装配尺度，连续三向投射与绑定法线共同驱动。无需重展原UV，移动／旋转部件后旧化位置仍锁在本地。三向投射在Blender由物理高度生成基础／涂层法线，避免把切线Normal直接接到不对应的UV上；原生OpenGL法线仍可导出供普通平铺UV使用。

高度标尺：喷漆纹理完整范围45µm、掉漆台阶约75µm、锈细孔120µm标尺、浅划痕20µm、附着脏渍16µm。均为着色起伏，不改几何。

实物细节源为[Poly Haven Rust Coarse 01](https://polyhaven.com/a/rust_coarse_01)，[CC0许可](https://polyhaven.com/license)。原始8K颜色／粗糙度／位移保留；仅多色及高通微细内容重新映射到12cm内容尺寸，没有把扫描板材的宏观起伏贴到椅子。来源与校验和见 `02_assets/textures/external/polyhaven_chair_metal/manifest.json`。

制作入口：`07_pipeline/scripts/chair_metal_sd.py`。当前实时应用与评审：`06_review/chair_metal_layers_20261001/report.md`。
