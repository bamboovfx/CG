"""Preview stronger broad figure patterns on the Tripo seat veneer."""

import bpy
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")


def linear(value):
    """Convert one 8-bit sRGB channel to Blender's linear color value."""
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def color(hex_value):
    """Return a linear RGBA value from an observed wood-color candidate."""
    return tuple(linear(int(hex_value[index:index + 2], 16)) for index in (1, 3, 5)) + (1.0,)


for shape, weight, dark, light, scale, distortion in (
    ("soft_a", 0.32, "#A56329", "#DEA04B", 3.0, 6.0),
    ("soft_b", 0.38, "#A56329", "#DEA04B", 4.0, 8.0),
):
    bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_uv.blend"))
    scene = bpy.context.scene
    scene.camera.location.z += 0.18
    scene.camera.data.ortho_scale = 0.72
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.cycles.samples = 40
    material = bpy.data.materials["AITA honey varnish / seat"]
    nodes = material.node_tree.nodes
    wave = next(node for node in nodes if node.type == "TEX_WAVE")
    ramp = next(node for node in nodes if node.type == "VALTORGB" and abs(node.color_ramp.elements[0].position - 0.22) < 0.001)
    mixture = next(node for node in nodes if node.type == "MIX_RGB" and abs(node.inputs[0].default_value - 0.24) < 0.001)

    # Reduce the strong band contrast, then distort the broad figure gently.
    mixture.inputs[0].default_value = weight
    ramp.color_ramp.elements[0].color = color(dark)
    ramp.color_ramp.elements[1].color = color(light)
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = distortion
    scene.render.filepath = str(BASE / f"diagnose_figure_{shape}.png")
    bpy.ops.render.render(write_still=True)
