"""Render isolated shader variants to locate the baked seat highlight."""

import bpy
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_baked.blend"))
scene = bpy.context.scene
scene.camera.location.z += 0.18
scene.camera.data.ortho_scale = 0.72
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.cycles.samples = 40
material = bpy.data.materials["Baked Wood PBR"]
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")


def render(label):
    """Render one material state to a named diagnosis image."""
    scene.render.filepath = str(BASE / f"diagnose_{label}.png")
    bpy.ops.render.render(write_still=True)


# A missing normal link checks whether tangent shading creates the bright patch.
normal_link = shader.inputs["Normal"].links[0]
material.node_tree.links.remove(normal_link)
render("without_normal")

# The next variant keeps the same geometry and maps but removes clear coat.
shader.inputs["Coat Weight"].default_value = 0.0
render("without_normal_coat")
