"""Compare the authored chair shader before and after mesh triangulation."""

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

# Keep camera and lighting fixed so only triangle conversion changes the view.
scene.render.filepath = str(BASE / "diagnose_authored_untriangulated.png")
bpy.ops.render.render(write_still=True)
for obj in scene.objects:
    if obj.type != "MESH" or not obj.name.startswith("LP_part_"):
        continue
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Triangulate", "TRIANGULATE")
    modifier.quad_method = "BEAUTY"
    bpy.ops.object.modifier_apply(modifier=modifier.name)
scene.render.filepath = str(BASE / "diagnose_authored_triangulated.png")
bpy.ops.render.render(write_still=True)

# Reopen the same source and preserve custom split normals during conversion.
bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_uv.blend"))
scene = bpy.context.scene
scene.camera.location.z += 0.18
scene.camera.data.ortho_scale = 0.72
scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.cycles.samples = 40
for obj in scene.objects:
    if obj.type != "MESH" or not obj.name.startswith("LP_part_"):
        continue
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Triangulate", "TRIANGULATE")
    modifier.quad_method = "BEAUTY"
    modifier.keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
scene.render.filepath = str(BASE / "diagnose_authored_triangulated_preserved.png")
bpy.ops.render.render(write_still=True)
