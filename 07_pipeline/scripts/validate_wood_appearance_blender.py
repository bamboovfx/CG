"""重开新版，验证实际节点接线、打包资源、参数和受保护几何／工艺组。"""
from pathlib import Path
import json
import hashlib
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_appearance_blender import process_signature,mesh_digest,PARAMS
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_appearance_20260930'
audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/audit['blend']))
checks={}; boards={}; images=set()
for obj,board in [('LP_part_02','seat'),('LP_part_09','back')]:
    ob=bpy.data.objects[obj]; t=ob.data.materials[0].node_tree
    proc=next(n for n in t.nodes if n.get('wood_layers_role')=='process')
    app=next(n for n in t.nodes if n.get('wood_layers_role')=='appearance')
    shader=next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED')
    checks[board+'_geometry_uv_normals']=mesh_digest(ob)==audit['geometry_before'][obj]
    checks[board+'_process_signature']=process_signature(proc.node_tree)==audit['process_before'][board]
    checks[board+'_controls']=all(abs(app.inputs[k].default_value-v)<1e-6 for k,v in PARAMS.items())
    checks[board+'_surface_links']=all(any(l.from_node==app and l.from_socket.name==source and l.to_node==shader and l.to_socket.name==target for l in t.links)
        for source,target in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Coat','Coat Weight'),('Normal','Coat Normal'),('Roughness','Coat Roughness')])
    checks[board+'_process_metallic']=any(l.from_node==proc and l.from_socket.name=='Metallic' and l.to_node==shader and l.to_socket.name=='Metallic' for l in t.links)
    bumps=[n for n in app.node_tree.nodes if n.type=='BUMP']
    checks[board+'_three_relief_layers']=len(bumps)==3 and sorted(round(n.inputs['Distance'].default_value,7) for n in bumps)==[.0001,.00012,.00022]
    for group in (proc.node_tree,app.node_tree):
        for n in group.nodes:
            if n.type=='TEX_IMAGE': images.add(n.image)
    boards[board]={'material':ob.data.materials[0].name,'process_group':proc.node_tree.name,'appearance_group':app.node_tree.name,
        'controls':{k:app.inputs[k].default_value for k in PARAMS},'relief':{n.get('wood_layers_role'):n.inputs['Distance'].default_value for n in bumps}}
checks['all_used_images_packed']=all(im.packed_file for im in images)
checks['correct_colour_spaces']=all(im.colorspace_settings.name==('sRGB' if 'BaseColor' in im.name else 'Non-Color') for im in images)
checks['input_unchanged']=hashlib.sha256((ROOT/audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
sc=bpy.context.scene
checks['perspective_camera']=sc.camera.data.type=='PERSP'
lights=[ob for ob in sc.objects if ob.type=='LIGHT']
checks['three_original_lights']=len(lights)==3 and sorted(ob.data.energy for ob in lights)==[15,45,55]
assert all(checks.values()),checks
result={'checks':checks,'passed':len(checks),'boards':boards,'used_images':len(images),'blend_sha256':hashlib.sha256((ROOT/audit['blend']).read_bytes()).hexdigest()}
(OUT/'reopen_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('REOPEN_CHECKS '+json.dumps(result,ensure_ascii=False),flush=True)
