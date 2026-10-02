"""以相同的帧、相机和采样渲染迁移前后工程，检查迁移是否改变画面。"""
import json
import sys
from pathlib import Path

import bpy


ROOT = Path("D:/00_projects/10_CG/Shot_Test")
OUT = ROOT / "06_review/classroom_pipeline_migration_20260929"
LABEL = sys.argv[-1]
assert LABEL in {"before", "after"}, LABEL

scene = bpy.context.scene
assert scene.name == "sq010_sh010"
assert scene.camera is not None
assert scene.frame_current == 1076

# 使用同一较低评审设置；不改变已保存工程的正式渲染参数。
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.seed = 23
scene.render.resolution_x = 960
scene.render.resolution_y = 405
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUT / f"{LABEL}.png")
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == "OPTIX"
scene.cycles.device = "GPU"

OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)
(OUT / f"{LABEL}.json").write_text(
    json.dumps(
        {
            "blend": bpy.data.filepath,
            "frame": scene.frame_current,
            "camera": scene.camera.name,
            "resolution": [960, 405],
            "samples": 32,
            "seed": 23,
            "output": scene.render.filepath,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf8",
)
