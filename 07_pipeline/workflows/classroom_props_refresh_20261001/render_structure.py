"""Render untouched Tripo geometry from six views for structural inspection.

Input: asset_parts.blend from audit_raw.py. Output: neutral geometry PNGs.
The shot and its materials remain outside this isolated inspection file.
"""
import bpy
import sys
from pathlib import Path
from mathutils import Vector


def aim(obj, target):
    """Aim a camera/light object at target; update its rotation in place."""
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def make_light(name, location, power, size, target):
    """Create an area light from position/power/size; return the linked object."""
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


base = Path(__file__).parent
asset = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=str(base / f'{asset}_parts.blend'))
scene = bpy.context.scene
meshes = [obj for obj in scene.objects if obj.type == 'MESH']
points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
lo = Vector([min(point[axis] for point in points) for axis in range(3)])
hi = Vector([max(point[axis] for point in points) for axis in range(3)])
center = (lo + hi) * 0.5
height = max(hi - lo)

# Neutral surface exposes geometry independently of generated baked shading.
material = bpy.data.materials.new('Material')
material.diffuse_color = (0.48, 0.48, 0.48, 1)
material.use_nodes = True
material.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 0.65
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('World')
scene.world.color = (0.12, 0.12, 0.12)
scene.view_settings.view_transform = 'AgX'
make_light('Area', center + Vector((-2, -3, 3)) * height, 900, 3 * height, center)
make_light('Area.001', center + Vector((3, -1, 1)) * height, 450, 3 * height, center)
make_light('Area.002', center + Vector((0, 3, 2)) * height, 700, 2 * height, center)
camera_data = bpy.data.cameras.new('Camera')
camera = bpy.data.objects.new('Camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = height * 1.3
output = base / f'{asset}_structure'
output.mkdir(exist_ok=True)

# Both opposite elevations avoid presuming the FBX front-axis convention.
views = {'front': (0, -4, 0), 'back': (0, 4, 0),
         'left': (-4, 0, 0), 'right': (4, 0, 0),
         'left45': (-3, -3, 1.0), 'right45': (3, -3, 1.0)}
for name, direction in views.items():
    camera.location = center + Vector(direction) * height
    aim(camera, center)
    scene.render.filepath = str(output / f'{name}.png')
    bpy.ops.render.render(write_still=True)
