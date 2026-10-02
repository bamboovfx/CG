"""重开新增脏渍候选，验证保护摘要、末端实际接线和全部使用贴图打包。"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_dirt_blender import snapshot
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_dirt_20260930'
audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/audit['blend']))
checks={'protected_geometry_uv_normals_process_appearance_controls':snapshot()==audit['protected']}
used=set(); board_records={}
for obj,board in [('LP_part_02','seat'),('LP_part_09','back')]:
    tree=bpy.data.objects[obj].data.materials[0].node_tree
    app=next(n for n in tree.nodes if n.get('wood_layers_role')=='appearance')
    proc=next(n for n in tree.nodes if n.get('wood_layers_role')=='process')
    dirt=next(n for n in tree.nodes if n.get('wood_layers_role')=='surface_dirt')
    shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
    checks[board+'_independent_strength']=dirt.inputs['Dirt'].default_value==1
    checks[board+'_previous_outputs_feed_dirt']=all(any(l.from_node==app and l.to_node==dirt and l.from_socket.name==name and l.to_socket.name==name for l in tree.links) for name in ['Color','Roughness','Normal','Coat','Coat Roughness'])
    checks[board+'_dirt_actual_shader_links']=all(any(l.from_node==dirt and l.to_node==shader and l.from_socket.name==a and l.to_socket.name==b for l in tree.links) for a,b in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Normal','Coat Normal'),('Coat','Coat Weight'),('Coat Roughness','Coat Roughness')])
    checks[board+'_metallic_unchanged']=any(l.from_node==proc and l.to_node==shader and l.to_socket.name=='Metallic' for l in tree.links)
    new_images=[n.image for n in dirt.node_tree.nodes if n.type=='TEX_IMAGE']
    checks[board+'_four_actual_4k_textures']=len(new_images)==4 and all(tuple(im.size)==(4096,4096) for im in new_images)
    checks[board+'_colour_space']=all(im.colorspace_settings.name==('sRGB' if 'DirtColor' in im.name else 'Non-Color') for im in new_images)
    bump=next(n for n in dirt.node_tree.nodes if n.type=='BUMP')
    checks[board+'_shallow_surface_relief']=abs(bump.inputs['Distance'].default_value-.000025)<1e-9
    for group in [proc.node_tree,app.node_tree,dirt.node_tree]:
        for n in group.nodes:
            if n.type=='TEX_IMAGE': used.add(n.image)
    board_records[board]={'group':dirt.node_tree.name,'node':dirt.name,'strength':dirt.inputs['Dirt'].default_value,'images':[im.name for im in new_images]}
checks['all_used_images_packed']=all(im.packed_file for im in used)
checks['source_unchanged']=hashlib.sha256((ROOT/audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
checks['perspective']=bpy.context.scene.camera.data.type=='PERSP'
checks['three_studio_lights']=sorted(ob.data.energy for ob in bpy.context.scene.objects if ob.type=='LIGHT')==[15,45,55]
assert all(checks.values()),checks
result={'checks':checks,'passed':len(checks),'used_images':len(used),'boards':board_records,'blend_sha256':hashlib.sha256((ROOT/audit['blend']).read_bytes()).hexdigest()}
(OUT/'reopen_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('SURFACE_DIRT_REOPEN '+json.dumps(result,ensure_ascii=False),flush=True)
