"""独立重开验证两种实际异常已消除、侧壁米制UV非退化及已认可表面保持。"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fix_wood_side_back import geometry_protection,BOARDS
from tripo_wood_appearance_blender import process_signature
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'06_review/tripo_wood_side_back_20260930'
audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/audit['blend']))
checks={}; details={}; used=set()
for obj,board,_,_ in BOARDS:
    ob=bpy.data.objects[obj]; m=ob.data; t=m.materials[0].node_tree; edge=m.materials[1].node_tree
    proc=next(n for n in t.nodes if n.get('wood_layers_role')=='process')
    dirt=next(n for n in t.nodes if n.get('wood_layers_role')=='surface_dirt')
    app=next(n for n in t.nodes if n.get('wood_layers_role')=='appearance')
    checks[board+'_geometry_all_original_uv_normals']=geometry_protection(ob)==audit['geometry_original_uv_normals'][board]
    checks[board+'_approved_process']=process_signature(proc.node_tree)==audit['process'][board]
    checks[board+'_approved_surface_dirt']=process_signature(dirt.node_tree)==audit['dirt'][board]
    checks[board+'_age_wear_scratches_controls']=all(abs(app.inputs[k].default_value-v)<1e-6 for k,v in audit['appearance_controls'][board].items())
    # 回归检查实际使用的矩形混合因子，而非只检查修复自定义属性。
    stamp=next(n for n in app.node_tree.nodes if n.get('wood_layers_role')=='rear_stamp_preserved')
    checks[board+'_legacy_rect_colour_disabled']=not stamp.inputs[0].is_linked and stamp.inputs[0].default_value==0
    checks[board+'_actual_edge_uv_used']=any(n.type=='UVMAP' and n.uv_map=='UV_WoodEdge' and n.outputs['UV'].is_linked for n in edge.nodes)
    checks[board+'_one_axis_sine_removed']=not any(n.type=='MATH' and n.operation=='SINE' for n in edge.nodes)
    m.calc_loop_triangles(); layer=m.uv_layers['UV_WoodEdge']; ratios=[]; anisotropy=[]
    for tri in m.loop_triangles:
        if m.polygons[tri.polygon_index].material_index!=1: continue
        a=np.array([m.vertices[k].co[:] for k in tri.vertices]); u=np.array([layer.data[l].uv[:] for l in tri.loops])
        x=a[1]-a[0]; x/=np.linalg.norm(x); normal=np.cross(a[1]-a[0],a[2]-a[0])
        if np.linalg.norm(normal)<1e-10: continue
        normal/=np.linalg.norm(normal); y=np.cross(normal,x)
        world=np.array([[np.dot(a[1]-a[0],x),np.dot(a[2]-a[0],x)],[np.dot(a[1]-a[0],y),np.dot(a[2]-a[0],y)]])
        tex=np.column_stack([u[1]-u[0],u[2]-u[0]])
        singular=np.linalg.svd(tex@np.linalg.inv(world),compute_uv=False)
        ratios.append(float(np.prod(singular))); anisotropy.append(float(singular[0]/max(singular[1],1e-12)))
    checks[board+'_side_uv_noncollapsed']=bool(ratios) and min(ratios)>.8
    checks[board+'_side_uv_stretch_limited']=max(anisotropy)<1.2
    checks[board+'_original_bake_uv_still_active']=[u.name for u in m.uv_layers if u.active_render]==['UV_Material']
    details[board]={'side_triangles':len(ratios),'uv_area_ratio_min':min(ratios),'uv_area_ratio_max':max(ratios),'maximum_anisotropy':max(anisotropy)}
    for group in [proc.node_tree,app.node_tree,dirt.node_tree]:
        for n in group.nodes:
            if n.type=='TEX_IMAGE': used.add(n.image)
checks['all_existing_images_packed']=all(im.packed_file for im in used)
checks['latest_input_not_overwritten']=hashlib.sha256((ROOT/audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
checks['perspective']=bpy.context.scene.camera.data.type=='PERSP'
assert all(checks.values()),checks
result={'checks':checks,'passed':len(checks),'side_uv':details,'used_images':len(used),'blend_sha256':hashlib.sha256((ROOT/audit['blend']).read_bytes()).hexdigest()}
(OUT/'reopen_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('SIDE_BACK_REOPEN '+json.dumps(result,ensure_ascii=False),flush=True)
