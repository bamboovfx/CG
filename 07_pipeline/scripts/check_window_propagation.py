"""重开候选/正式源，核对统一范围、原位保护、凹槽深度、五金净空和依赖。"""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from propagate_window_standard import fingerprint,center,ROOT,CACHE,OUT,SCOPES
from correct_window_hardware import evaluated_bvh

report=json.loads((OUT/'candidate.json').read_text(encoding='utf-8'))
before=json.loads((CACHE/'before_fingerprint.json').read_text(encoding='utf-8'));after=fingerprint()
protected=set(before)-set(report['removed'])-set(report['modified'])
changed=[n for n in protected if before[n]!=after.get(n)]
moved=[n for n in before if n not in report['removed'] and before[n]['matrix']!=after[n]['matrix']]
drains=[o.name for c in SCOPES for o in bpy.data.collections[c].objects if not o.hide_render and 'drain' in o.name.lower()]
locks=[o for c in SCOPES for o in bpy.data.collections[c].objects if not o.hide_render and o.name.startswith('ARC crescent lock escutcheon')]
legacy=[o.name for o in locks if o.type!='MESH' or not any(m and m.name.startswith('Hardware / Satin metal baked') for m in o.data.materials)]
depths=[];holes=[];intersections=[]
for g in report['groups']:
    cam=bpy.data.objects[g['parts'][2]];outer=bpy.data.objects[g['outer']]
    # 仅检测不应接触的窗框，搭接锁扣和底座贴合不作为穿插误报。
    count=len(evaluated_bvh(cam).overlap(evaluated_bvh(outer)))
    if count:intersections.append({'cam':cam.name,'outer':outer.name,'faces':count})
for ob in bpy.data.objects:
    if ob.name.startswith('REF recessed finger pull') and '/ recess' not in ob.name and ob.get('window_standard'):
        stile=ob.parent;sc=center(stile);face=sc.x-stile.dimensions.x/2;pc=center(ob)
        hit= evaluated_bvh(stile).ray_cast(Vector((face-.02,sc.y,pc.z)),Vector((1,0,0)),.06)
        depth=hit[0].x-face if hit[0] else None
        depths.append(depth)
        if depth is None or not .005<depth<.006:holes.append({'name':ob.name,'depth':depth})
missing=[bpy.path.abspath(i.filepath,library=i.library) for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file and not Path(bpy.path.abspath(i.filepath,library=i.library)).exists()]
validation={'file':bpy.data.filepath,'lock_count':len(locks),'legacy_locks':legacy,'remaining_visible_drains':drains,
            'non_target_changes':changed,'existing_objects_moved':moved,'pocket_count':len(depths),'bad_pockets':holes,
            'cam_frame_intersections':intersections,'missing_textures':missing,
            'passed':len(locks)==36 and len(depths)==60 and not any([legacy,drains,changed,moved,holes,intersections,missing])}
label=sys.argv[sys.argv.index('--')+1]
(OUT/(label+'.json')).write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
