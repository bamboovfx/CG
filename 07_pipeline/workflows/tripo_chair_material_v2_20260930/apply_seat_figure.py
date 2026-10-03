"""Apply the approved soft wood figure to the existing final UV source."""

import bpy
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")


def linear(value):
    """Convert an 8-bit sRGB channel to Blender's linear color value."""
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def color(hex_value):
    """Return the RGBA color for an observed wood palette candidate."""
    return tuple(linear(int(hex_value[index:index + 2], 16)) for index in (1, 3, 5)) + (1.0,)


bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_uv.blend"))
material = bpy.data.materials["AITA honey varnish / seat"]
nodes = material.node_tree.nodes
wave = next(node for node in nodes if node.type == "TEX_WAVE")
ramp = next(node for node in nodes if node.type == "VALTORGB" and abs(node.color_ramp.elements[0].position - 0.22) < 0.001)
mixture = next(node for node in nodes if node.type == "MIX_RGB" and abs(node.inputs[0].default_value - 0.24) < 0.001)

# Keep the reference's broad variation without turning it into regular stripes.
wave.inputs["Distortion"].default_value = 6.0
mixture.inputs[0].default_value = 0.32
ramp.color_ramp.elements[0].color = color("#A56329")
ramp.color_ramp.elements[1].color = color("#DEA04B")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(BASE / "chair_material_v2_uv.blend"))
