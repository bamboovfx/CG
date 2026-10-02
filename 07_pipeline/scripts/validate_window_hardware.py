"""重开已保存建筑源，验证硬表面几何、布尔依赖、滑动净空和外部贴图。"""
import bpy
import bmesh
import json
import runpy
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
module=runpy.run_path(str(ROOT/'07_pipeline/scripts/correct_window_hardware.py'))
report=json.loads((ROOT/'06_review/window_hardware_correction/candidate_validation.json').read_text(encoding='utf-8'))
geometry=[]
# 用拓扑检查锁杯的真实壁厚实体，而不是仅依赖看起来有体积的渲染。
for group in report['groups']:
    ob=bpy.data.objects[group['cam']]
    bm=bmesh.new(); bm.from_mesh(ob.data)
    geometry.append({'object':ob.name,'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=False)})
    bm.free()
booleans=[{'object':o.name,'cutter':m.object.name if m.object else None}
          for o in bpy.data.collections['AST_window_wall_left'].objects
          for m in o.modifiers if m.type=='BOOLEAN' and m.object and m.object.get('window_hardware_20260927')]
# 射线检查槽底深度，验证隐藏切割体仍参与求值且孔槽是真实几何。
pockets=[]
for item in booleans:
    ob=bpy.data.objects[item['object']]; cutter=bpy.data.objects[item['cutter']]
    sc=module['center'](ob); z=cutter.matrix_world.translation.z
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); inv=eo.matrix_world.inverted()
    origin=Vector((sc.x+.0285,sc.y,z)); direction=Vector((-1,0,0))
    hit,loc,normal,index=eo.ray_cast(inv@origin,inv.to_3x3()@direction)
    depth=(sc.x+.0185-(eo.matrix_world@loc).x) if hit else None
    pockets.append({'object':ob.name,'depth':depth,'cutter_hidden':cutter.hide_viewport and cutter.hide_render})
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file
         and not Path(bpy.path.abspath(i.filepath,library=i.library)).exists()]
motion=module['validate_motion'](report)
result={'file':bpy.data.filepath,'geometry':geometry,'editable_pockets':booleans,'pocket_depths':pockets,'missing_images':missing,
        'motion':motion,'controller_y':bpy.data.objects['ctrl_window_left_04'].location.y,
        'passed':all(r['non_manifold_edges']==0 and r['volume']>0 for r in geometry)
                 and len(booleans)==12 and all(p['depth'] and p['depth']>.004 and p['cutter_hidden'] for p in pockets)
                 and not missing and not any(r['intersections'] for r in motion)}
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['reopened_candidate.json']
(ROOT/'06_review/window_hardware_correction'/args[0]).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result))
