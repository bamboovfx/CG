"""重开扫描辅助候选，验证资源、真实接线、参数、受保护几何和工艺。"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_detail_blender import PARAMS
from tripo_wood_appearance_blender import mesh_digest,process_signature
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_detail_20260930'
audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/audit['blend']))
checks={}; used=set(); boards={}
for obj,board in [('LP_part_02','seat'),('LP_part_09','back')]:
    ob=bpy.data.objects[obj]; t=ob.data.materials[0].node_tree
    proc=next(n for n in t.nodes if n.get('wood_layers_role')=='process')
    app=next(n for n in t.nodes if n.get('wood_layers_role')=='appearance')
    shader=next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED')
    checks[board+'_geometry_uv_normals']=mesh_digest(ob)==audit['geometry_before'][obj]
    checks[board+'_process_preserved']=process_signature(proc.node_tree)==audit['process_before'][board]
    checks[board+'_controls']=all(abs(app.inputs[k].default_value-v)<1e-6 for k,v in PARAMS.items())
    checks[board+'_actual_links']=all(any(l.from_node==app and l.from_socket.name==source and l.to_node==shader and l.to_socket.name==target for l in t.links)
        for source,target in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Coat','Coat Weight'),('Normal','Coat Normal'),('Coat Roughness','Coat Roughness')])
    checks[board+'_metallic_process']=any(l.from_node==proc and l.from_socket.name=='Metallic' and l.to_node==shader and l.to_socket.name=='Metallic' for l in t.links)
    colours=[n for n in app.node_tree.nodes if n.type=='TEX_IMAGE' and n.get('wood_layers_role') in ('AgeColor','WearColor','DirtColor')]
    checks[board+'_three_real_colour_maps']=len(colours)==3 and all(tuple(n.image.size)==(4096,4096) for n in colours)
    bumps=[n for n in app.node_tree.nodes if n.type=='BUMP']
    checks[board+'_four_relief_layers']=len(bumps)==4 and sorted(round(n.inputs['Distance'].default_value,7) for n in bumps)==[.00003,.0001,.00012,.00022]
    for group in (proc.node_tree,app.node_tree):
        for n in group.nodes:
            if n.type=='TEX_IMAGE': used.add(n.image)
    boards[board]={'material':ob.data.materials[0].name,'appearance_group':app.node_tree.name,
        'parameters':{k:app.inputs[k].default_value for k in PARAMS},'image_sources':[n.image.filepath for n in colours]}
checks['all_used_images_packed']=all(im.packed_file for im in used)
checks['actual_colour_spaces']=all(im.colorspace_settings.name==('sRGB' if 'Color' in im.name else 'Non-Color') for im in used)
checks['source_unchanged']=hashlib.sha256((ROOT/audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
sc=bpy.context.scene; checks['perspective']=sc.camera.data.type=='PERSP'
checks['original_three_lights']=sorted(ob.data.energy for ob in sc.objects if ob.type=='LIGHT')==[15,45,55]
assert all(checks.values()),checks
result={'checks':checks,'passed':len(checks),'used_images':len(used),'boards':boards,'blend_sha256':hashlib.sha256((ROOT/audit['blend']).read_bytes()).hexdigest()}
(OUT/'reopen_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('WOOD_DETAIL_REOPEN '+json.dumps(result,ensure_ascii=False),flush=True)
