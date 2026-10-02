"""Align cabinet grain and close the door reveals after SD scan processing, preserving placement."""
import bpy,json
from pathlib import Path
root=Path('D:/00_projects/10_CG/Shot_Test');source=root/'02_assets/work/classroom_equipment.blend'
for name in ['EQ SD varnished_wood','EQ SD exposed_wood']:
 m=bpy.data.materials[name];m['tile_metres']=.6;m['wood_scan_source']='CC0 Poly Haven plywood; genuinely processed in native SBS'
 for n in m.node_tree.nodes:
  if n.bl_idname=='ShaderNodeVectorMath' and n.operation=='SCALE':n.inputs[3].default_value=1/.6
for o in bpy.data.collections['AST_equipment_cabinet'].all_objects:
 if o.type!='MESH':continue
 if any(s.material and s.material.name in ['EQ SD varnished_wood','EQ SD exposed_wood'] for s in o.material_slots):
  # The original source scan grows along U; edit the real UVs so tangent normals follow the same direction.
  for d in o.data.uv_layers[0].data:d.uv=(d.uv.y,d.uv.x)
 if o.name.startswith('EQ wood door vertical stile') or o.name.startswith('EQ wood door flush inset panel'):
  for v in o.data.vertices:
   if v.co.z>.59:v.co.z+=.0045
 elif o.name.startswith('EQ wood door horizontal rail'):
  if min(v.co.z for v in o.data.vertices)>.5:
   for v in o.data.vertices:v.co.z+=.0045
for im in bpy.data.images:
 if im.source=='FILE':im.reload()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
