import bpy, json
from pathlib import Path
r={}
for o in bpy.context.scene.objects:
 if any(s in o.name.lower() for s in ['clock','board','teaching']):
  r[o.name]={'loc':list(o.matrix_world.translation),'collection':o.instance_collection.name if o.instance_collection else None,'offset':list(o.instance_collection.instance_offset) if o.instance_collection else None}
Path('D:/00_projects/10_CG/Shot_Test/06_review/production_audit_20260920/character/camera_landmarks_probe.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(r)
