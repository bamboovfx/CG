# CRT 屏幕分层污渍

用 Substance 3D Designer 打开 `tv_screen_imperfection.sbs`。节点来自本机 Adobe 原生库，保留默认节点名称，用独立注释说明各层用途。SBSAR 为同图编译版本。

本图是参照用户提供的 Sony CRT 作品进行的程序化表面研究，不是扫描材质，也未使用参考图片像素。

## 参数

- `BaseRoughness`：干净玻璃粗糙度，默认 0.035。
- `DepositAmount`：干燥残留对粗糙度的影响，默认 0.45。
- `OilAmount`：油膜对粗糙度的影响，默认 0.40。
- `WipeAmount`：擦拭对粗糙度的影响，默认 0.08。
- `ScratchAmount`：划痕对粗糙度的影响，默认 0.38。
- `LongScratchAmount` / `CrossScratchAmount` / `ScuffAmount`：长划痕、交叉细痕、局部擦伤的合成强度，默认 0.65 / 0.40 / 0.20。

修改这些参数后，需要重新导出贴图，再在 Blender 中重新加载图片。前五个参数主要控制最终 Roughness 输出，不直接缩放独立原始掩码。

## 输出与 Blender

10 个输出：DustMask、DepositMask、OilMask、WipeMask、MicroScratches、LongScratches、ScuffMask、ScratchMask、Roughness、Height。均为 4K、16 位灰度，使用 Non-Color。

玻璃材质：`TV glass / SD layered deposits`。Roughness 直接驱动透射玻璃；DepositMask × 0.30 与 WipeMask × 0.02 控制薄沉积层；Height 驱动弱 Bump（Distance 0.000006 m、Strength 0.15），无需给玻璃添加宏观置换。

共享外壳：`TV shell / User finish`。仅替换划痕及擦拭输入，并在原有法线之后加入微弱划痕 Bump；原有颜色节点与数值保留。

实际映射：SurfaceMeters UV × 1.25，一个贴图周期对应 0.8 m。屏幕与外壳采用不同偏移，避免痕迹位置完全一致。

可重复构建脚本：`07_pipeline/scripts/tv_screen_imperfection_sd.py`。编译工具为 Adobe sbscooker / sbsrender（d3d11），贴图与哈希记录见 generated/tv_screen_imperfection/manifest.json。
