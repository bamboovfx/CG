"""Render four consistent orthographic reference views from the existing chair.

Input: classroom_props.blend. Outputs: four PNG files, a candidate .blend and JSON.
The original source file is opened read-only and never saved.
"""

import bpy
import json
import math
import sys
from mathutils import Vector
from pathlib import Path


OUTPUT_DIR = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")
PART_COLLECTIONS = ("chair_hp_frame", "chair_hp_wood", "chair_hp_hardware", "chair_hp_feet")


def get_part_objects():
    """Return only the four high-poly production-part groups, without edge references."""
    found = []
    seen = set()
    for name in PART_COLLECTIONS:
        collection = bpy.data.collections[name]
        for obj in collection.all_objects:
            if obj.type == "MESH" and obj.name not in seen:
                found.append(obj)
                seen.add(obj.name)
    return found


def world_bounds(objects):
    """Return the world-space bounding minimum and maximum of input objects."""
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    return (
        Vector(tuple(min(c[index] for c in corners) for index in range(3))),
        Vector(tuple(max(c[index] for c in corners) for index in range(3))),
    )


def make_scene(objects):
    """Create a self-contained candidate scene linked to the selected source objects."""
    scene = bpy.data.scenes.new("Tripo chair four-view reference")
    parts = bpy.data.collections.new("Chair parts")
    scene.collection.children.link(parts)
    for obj in objects:
        parts.objects.link(obj)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.world = bpy.data.worlds.new("Four-view neutral world")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)
    background.inputs[1].default_value = 0.35
    return scene


def add_area_light(scene, location, energy, size):
    """Add one neutral area light at location with the given watts and size."""
    data = bpy.data.lights.new("Area", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new("Area", data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 0.4)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def render_view(scene, camera, target, direction, view_name, ortho_scale):
    """Place an orthographic camera on a principal axis and save one PNG."""
    camera.location = target + direction * 2.5
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = ortho_scale
    scene.render.filepath = str(OUTPUT_DIR / f"chair_{view_name}.png")
    bpy.ops.render.render(scene=scene.name, write_still=True)


def main():
    """Build the isolated scene, render four matching views and write provenance."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_path = bpy.data.filepath
    objects = get_part_objects()
    bounds_min, bounds_max = world_bounds(objects)
    center = (bounds_min + bounds_max) / 2
    size = bounds_max - bounds_min
    scene = make_scene(objects)
    camera_data = bpy.data.cameras.new("Orthographic Camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("Orthographic Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    add_area_light(scene, center + Vector((0.0, 1.2, 1.3)), 70, 1.5)
    add_area_light(scene, center + Vector((0.0, -1.0, 1.1)), 50, 1.5)
    # Keep every view at the same scale so the image heights can be compared.
    ortho_scale = max(size.x, size.y, size.z) * 1.22
    for name, direction in (
        ("front", Vector((0, 1, 0.25)).normalized()),
        ("left", Vector((-1, 0, 0.25)).normalized()),
        ("right", Vector((1, 0, 0.25)).normalized()),
        ("back", Vector((0, -1, 0.25)).normalized()),
    ):
        render_view(scene, camera, center, direction, name, ortho_scale)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_DIR / "chair_fourview_source.blend"))
    metadata = {
        "source": source_path,
        "part_collections": PART_COLLECTIONS,
        "object_count": len(objects),
        "bounds_m": {"min": list(bounds_min), "max": list(bounds_max), "size": list(size)},
        "views": ["front", "left", "right", "back"],
        "resolution": 1024,
        "orthographic_scale_m": ortho_scale,
    }
    (OUTPUT_DIR / "fourview_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("FOURVIEW_MANIFEST=" + json.dumps(metadata))


main()
