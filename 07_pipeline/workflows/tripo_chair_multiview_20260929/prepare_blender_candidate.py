"""Create an editable Tripo chair candidate with UVs and visual QC renders.

Input: original P2.0 FBX. Outputs: candidate .blend, Painter FBX, clay and UV grid PNGs.
No project source or shot file is changed.
"""

import bpy
import json
import sys
from mathutils import Vector
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")
INPUT = BASE / "tripo_chair_multiview_p2_quad_10000.fbx"
TARGET_HEIGHT = 0.8045


def make_material(name, color, image=None):
    """Return a simple editable Principled material, optionally with a UV grid."""
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1)
    principled.inputs["Roughness"].default_value = 0.62
    if image:
        image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
        image_node.image = image
        material.node_tree.links.new(image_node.outputs["Color"], principled.inputs["Base Color"])
    return material


def bounds(obj):
    """Return world-space minimum, maximum and size vectors of one mesh object."""
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high, high - low


def make_lighting(scene, target):
    """Add neutral world illumination, two area lights and one camera to a scene."""
    scene.world = bpy.data.worlds.new("Neutral world")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    background.inputs[1].default_value = 0.35
    for position, power in ((Vector((1.1, 1.4, 1.8)), 80), (Vector((-1.2, -0.6, 1.4)), 55)):
        lamp = bpy.data.lights.new("Area", "AREA")
        lamp.energy = power
        lamp.shape = "DISK"
        lamp.size = 1.4
        obj = bpy.data.objects.new("Area", lamp)
        scene.collection.objects.link(obj)
        obj.location = target + position
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera_data = bpy.data.cameras.new("Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 1.25
    camera = bpy.data.objects.new("Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = target + Vector((1.3, 1.7, 1.25))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def render(scene, filepath):
    """Write the currently visible candidate at the given image path."""
    scene.render.filepath = str(filepath)
    bpy.ops.render.render(write_still=True)


def main():
    """Import, size, unwrap, split, save and audit the candidate chair."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(INPUT))
    scene = bpy.context.scene
    source = next(obj for obj in scene.objects if obj.type == "MESH")
    source.name = "SOURCE Tripo P2.0 original"
    raw_collection = bpy.data.collections.new("SOURCE / untouched import")
    scene.collection.children.link(raw_collection)
    for collection in list(source.users_collection):
        collection.objects.unlink(source)
    raw_collection.objects.link(source)
    source.hide_render = True
    source.hide_set(True)
    low_collection = bpy.data.collections.new("LP / editable UV candidate")
    scene.collection.children.link(low_collection)
    low = source.copy()
    low.data = source.data.copy()
    low.name = "LP combined before split"
    low_collection.objects.link(low)
    low.hide_render = False
    low.hide_set(False)
    source_low, source_high, source_size = bounds(low)
    low.scale *= TARGET_HEIGHT / source_size.z
    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # One unwrap before splitting gives all pieces a shared 0-1 UV atlas.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")
    low.data.uv_layers.active.name = "UVMap"
    # Split disconnected geometry for selection and further manual repair.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [obj for obj in low_collection.objects if obj.type == "MESH"]
    for index, obj in enumerate(sorted(parts, key=lambda item: item.name)):
        obj.name = f"LP_part_{index:02d}"
        obj["source"] = "Tripo P2.0 multiview; 2026-09-29"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    # Keep one material and texture set for this test; the parts remain selectable.
    clay = make_material("QA clay", (0.62, 0.60, 0.56))
    grid = bpy.data.images.new("UV grid 2K", width=2048, height=2048, alpha=False)
    grid.generated_type = "COLOR_GRID"
    grid.pack()
    grid_material = make_material("QA UV grid", (1, 1, 1), grid)
    for obj in parts:
        obj.data.materials.clear()
        obj.data.materials.append(clay)
    low_point = Vector(tuple(min(bounds(obj)[0][axis] for obj in parts) for axis in range(3)))
    high_point = Vector(tuple(max(bounds(obj)[1][axis] for obj in parts) for axis in range(3)))
    target = (low_point + high_point) / 2
    make_lighting(scene, target)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    render(scene, BASE / "candidate_clay.png")
    for obj in parts:
        obj.data.materials.clear()
        obj.data.materials.append(grid_material)
    render(scene, BASE / "candidate_uv_grid.png")
    for obj in parts:
        obj.data.materials.clear()
        obj.data.materials.append(clay)
    # Save the source and low candidate in one editable file; export only low parts.
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BASE / "tripo_chair_blender_candidate.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.export_scene.fbx(
        filepath=str(BASE / "tripo_chair_painter_input.fbx"),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        bake_space_transform=False,
        path_mode="AUTO",
    )
    report = {
        "input": str(INPUT),
        "target_height_m": TARGET_HEIGHT,
        "actual_bounds_m": {"min": list(low_point), "max": list(high_point)},
        "part_count": len(parts),
        "vertices": sum(len(obj.data.vertices) for obj in parts),
        "faces": sum(len(obj.data.polygons) for obj in parts),
        "all_parts_have_uv": all(bool(obj.data.uv_layers) for obj in parts),
    }
    (BASE / "candidate_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CANDIDATE_AUDIT=" + json.dumps(report))


main()
