"""Render the exported Painter GLB under neutral lights for asset review."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim_at(obj, target):
    """Point obj toward target; obj is a camera or light and target is a 3D position."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_area_light(name, location, energy, size, target):
    """Create an area light at location with energy/size, aiming at target; return it."""
    light_data = bpy.data.lights.new(name=name, type="AREA")
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    aim_at(light, target)
    return light


def render(input_path, output_path):
    """Import input_path, set neutral review lighting, and render to output_path."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(input_path))
    scene = bpy.context.scene

    # Put the chair on a matte floor so floating geometry and contact issues are visible.
    floor_material = bpy.data.materials.new("review_floor")
    floor_material.diffuse_color = (0.18, 0.19, 0.21, 1.0)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.006))
    floor = bpy.context.object
    floor.name = "review_floor"
    floor.data.materials.append(floor_material)

    camera_data = bpy.data.cameras.new("review_camera")
    camera = bpy.data.objects.new("review_camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (1.55, -1.65, 1.30)
    aim_at(camera, (0, 0, 0.49))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 1.68
    scene.camera = camera

    add_area_light("key", (1.2, -1.0, 2.6), 175, 1.6, (0, 0, 0.5))
    add_area_light("fill", (-1.5, -0.2, 1.4), 75, 1.4, (0, 0, 0.5))
    add_area_light("rim", (-0.3, 1.3, 2.1), 110, 1.0, (0, 0, 0.5))
    scene.world = bpy.data.worlds.new("review_world")
    scene.world.color = (0.08, 0.08, 0.08)

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1 :]
    render(Path(args[0]), Path(args[1]))
