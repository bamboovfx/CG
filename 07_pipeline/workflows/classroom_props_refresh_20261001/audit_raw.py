"""Inspect exported Tripo FBX in an isolated Blender, without modifying the shot."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector

base = Path(__file__).parent
asset = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(base / f'{asset}_raw.fbx'))
objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for obj in objects:
    # Apply the FBX axis transform before measuring components.
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
report=[]
for i, obj in enumerate(parts):
    obj.name=f'{asset}_part_{i:02d}'
    points=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
    report.append({'name':obj.name,'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),
        'quad':sum(len(p.vertices)==4 for p in obj.data.polygons),'uv':len(obj.data.uv_layers),
        'min':[min(p[k] for p in points) for k in range(3)],
        'max':[max(p[k] for p in points) for k in range(3)]})
(base/f'{asset}_raw_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(base/f'{asset}_parts.blend'))
print(json.dumps({'asset':asset,'parts':len(parts),'faces':sum(r['faces'] for r in report)}))
