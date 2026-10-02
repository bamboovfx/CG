"""重开候选，检查真实网格封闭性、胶条厚度、玻璃及用户变换保护。"""
import bpy,bmesh,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import correct_window_glazing as w
r=json.loads((w.OUT/'candidate.json').read_text(encoding='utf8'))
before=json.loads((w.CACHE/'baseline.json').read_text(encoding='utf8'));now=w.fingerprint()
removed=set(r['removed']);modified=set(r['modified'])
unexpected=[n for n in before if n not in removed|modified and before[n]!=now.get(n)]
moved=[n for n in before if n not in removed and before[n]['matrix']!=now[n]['matrix']]
bad=[];seals=[]
for n in modified:
    o=bpy.data.objects[n];bm=bmesh.new();bm.from_mesh(o.data)
    if any(not e.is_manifold for e in bm.edges):bad.append(n)
    bm.free()
    if 'EPDM seal' in n:seals.append(o.dimensions.x)
glass_bad=[x['glass'] for x in r['panes'] if abs(bpy.data.objects[x['glass']].dimensions.x-.005)>.00001]
missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and im.filepath and not Path(bpy.path.abspath(im.filepath,library=im.library)).exists()]
stops=[o.name for c in w.SCOPES for o in bpy.data.collections[c].objects if not o.hide_render and o.name.startswith('REF rubber sash stop')]
result={'unexpected_changes':unexpected,'moved_objects':moved,'nonmanifold':bad,'wrong_glass_thickness':glass_bad,'missing_images':missing,'remaining_stops':stops,
 'panes':len(r['panes']),'seals':len(seals),'seal_depth_mm':[min(seals)*1000,max(seals)*1000],
 'control_y':bpy.data.objects['ctrl_window_left_04'].location.y,'lock_y':bpy.data.objects['ctrl_window_lock_02'].rotation_euler.y}
result['passed']=not any([unexpected,moved,bad,glass_bad,missing,stops])
(w.OUT/('published_validation.json' if 'classroom_environment' in bpy.data.filepath else 'validation.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False));assert result['passed']
