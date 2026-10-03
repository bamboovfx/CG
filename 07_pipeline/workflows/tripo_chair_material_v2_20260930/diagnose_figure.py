"""Compare seat figure strength against the observed broad wood grain."""

import bpy
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_uv.blend"))
scene = bpy.context.scene
scene.camera.location.z += 0.18
scene.camera.data.ortho_scale = 0.72
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.cycles.samples = 40
material = bpy.data.materials["AITA honey varnish / seat"]
figure_mix = next(
    node for node in material.node_tree.nodes
    if node.type == "MIX_RGB" and abs(node.inputs[0].default_value - 0.24) < 0.0001
)

# Keep the same camera and light for the two stronger figure candidates.
for weight in (0.32, 0.40):
    figure_mix.inputs[0].default_value = weight
    scene.render.filepath = str(BASE / f"diagnose_figure_{int(weight * 100)}.png")
    bpy.ops.render.render(write_still=True)
