"""用独立默认场景验证保存、重开和 CPU 渲染；不读取或改写正式场景。"""

from pathlib import Path
import json
import bpy


def main() -> None:
    """无参数；以 factory-startup 场景写入 .local/cloud-smoke，校验图像并生成结果摘要。"""
    if bpy.app.version[:3] != (5, 1, 2):
        raise RuntimeError(f"Expected Blender 5.1.2, got {bpy.app.version_string}")
    root = Path(__file__).resolve().parents[1]
    output = root / ".local" / "cloud-smoke"
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.render.resolution_x = scene.render.resolution_y = 64
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output / "smoke.png")
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "smoke.blend"), check_existing=False)
    bpy.ops.wm.open_mainfile(filepath=str(output / "smoke.blend"))
    assert bpy.context.scene.camera is not None and "Cube" in bpy.data.objects
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(output / "smoke.png"), check_existing=False)
    assert tuple(image.size) == (64, 64)
    colors = list(image.pixels)[0::4]
    assert max(colors) - min(colors) > 0.001, "Rendered image has no visible variation"
    result = {"blender": bpy.app.version_string, "save_reopen": True, "cpu_render": True,
              "size": [64, 64], "formal_scene_tested": False}
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
