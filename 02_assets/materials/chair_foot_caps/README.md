# 四个底部胶脚材质

参考用户原课椅照片，制作浅黄哑光模塑胶质；照片只用于观察，不采样为贴图。原生SD源 `chair_foot_caps.sbs`、编译包 `chair_foot_caps.sbsar`：66节点、18张4096×4096输出，8cm内容周期。程序生成内容的校验和位于 `02_assets/textures/generated/chair_foot_caps/manifest.json`。

工艺层包含BaseColor、Roughness、Metallic、Height、OpenGL Normal和AO。胶质始终Metallic=0、AO=1，实际遮蔽由场景渲染产生；粗糙度基准0.61、IOR=1.46，无清漆。细微表面高度完整标尺20µm。

表现层分别控制Age、Wear、Scratches、Dirt，作用于颜色、粗糙度和微凹凸。斑驳黄化、泛白擦伤、约0.2mm细划痕和底边不均匀灰污为当前外观；不使用金属锈蚀。默认Age=0.75、Wear=0.75、Scratches=0.70，四件Dirt分别0.65／0.60／0.70／0.63。全部归零恢复工艺层。

Blender四件各有独立根材质，共享工艺与表现内容组。9张实际使用贴图全部打包；显式三向投射及法线权重绑定原装配朝向，近地脏渍的高度包络绑定本胶脚。移动旋转对象时纹理跟随对象；原UV、网格与自定义法线保持。三向投射从Height生成法线，避免把导出的切线Normal接到不对应的UV；导出Normal可供普通平铺UV使用。

工艺／表现组说明位于注释框，原生节点保留默认名称。制作入口：`07_pipeline/scripts/chair_foot_caps_sd.py`、`chair_foot_caps_blender.py`。评审与验证：`06_review/chair_foot_cap_visibility_20261001/report.md`。
