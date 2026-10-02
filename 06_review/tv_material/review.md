# 电视材质参考与制作 · 2026-09-14

外形沿用已重做的消费级 CRT，按两组用户参考拆分表面使用痕迹。

- [Jyotirmay Dubey — Old TV](https://www.artstation.com/artwork/DvQ9Dn)：观察到深灰塑料、细颗粒、细划伤、边缘磨白、屏幕擦拭与灰尘残留。采用其磨损分布思路，没有复制贴图、模型或贴纸图案。
- [Sahaar Chhabra — Retro CRT 90’s Monitor](https://www.artstation.com/artwork/nE129e)：观察到屏幕斑驳反光、外壳细划伤、后盖和凹槽积灰、旧标签与接口的反射差异。未将专业监视器的金属外壳套用到这台塑料电视。

## 本次调整

前框、后壳、喇叭网、按键区分别使用独立材质。深灰 ABS 的 Metallic 为 0，前框基础 Roughness 为 0.47，后壳为 0.56；加上少量擦拭差异和局部积灰，磨损处局部降低粗糙度。插头、螺丝使用 Metallic 1，Roughness 约 0.24–0.37。塑料磨白仍然是塑料，不露银色金属。

使用 SurfaceMeters UV，既有 SD 数据以 0.4 m 周期映射。沿用 `clock_imperfection/Roughness.png` 和 `closeup_surface/closeup_polymer/Height.png`、`ScratchMask.png`。纹理均为 Non-Color。现有节点材质增加对象局部坐标下的有限划伤、棱边磨损、朝上表面与凹槽积灰。Noise 仅用于遮罩破碎和低幅度变化，没有将全范围噪声直接接入粗糙度。

玻璃保留曲面、透射和 IOR 1.52，用既有擦拭图控制约 0.055–0.205 的基础粗糙度，并在边缘增加薄污层。玻璃中心仍保留反射；此类关闭的 CRT 在教室强光下会反射周围墙面和窗户。

节点保留 Blender 默认名称，说明写在独立注释框中。没有更改模型、灯光或钟表材质，也没有新建或修改 SD 工程；这是 Blender 材质层调整与既有 SD 纹理复用。

## 检查与恢复

中性灯光下检查正面、背面与控制区；教室原灯光下检查近景。局部磨损比参考中最重的污损更克制，最终强度待用户视觉验收。

源文件：`02_assets/work/classroom_equipment.blend`。资产库：`02_assets/library/classroom_assets.blend`。

接回时只替换电视材质槽；几何、物体变换和其他物体的材质绑定通过哈希检查。材质旧版本和修改前源工程快照保留在 `07_pipeline/cache/tv_material`。打开中的镜头未重新连接，需要重新载入资产库查看。
