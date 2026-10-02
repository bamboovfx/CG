"""只读检查用户最新木椅候选：保留实际参数、相机、灯光和两块木板摘要。"""
from pathlib import Path
import sys
import json
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_reference_blender import mesh_digest
from tripo_wood_appearance_blender import process_signature
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930'
OUT.mkdir(parents=True,exist_ok=True)
result={'boards':{},'camera':{},'lights':[]}
for name,board in [('LP_part_02','seat'),('LP_part_09','back')]:
    # 读取当前接线及默认值，不根据旧报告恢复用户修改。
    ob=bpy.data.objects[name]; tree=ob.data.materials[0].node_tree
    groups={n.get('wood_layers_role'):n for n in tree.nodes if n.type=='GROUP'}
    result['boards'][board]={'geometry':mesh_digest(ob),'process':process_signature(groups['process'].node_tree),
        'appearance':process_signature(groups['appearance'].node_tree),
        'controls':{k:groups['appearance'].inputs[k].default_value for k in ['Age','Wear','Scratches']},
        'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
sc=bpy.context.scene
result['camera']={'location':list(sc.camera.location),'lens':sc.camera.data.lens,'type':sc.camera.data.type}
result['lights']=[{'name':ob.name,'energy':ob.data.energy,'location':list(ob.location)} for ob in sc.objects if ob.type=='LIGHT']
(OUT/'input_inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('DIRT_INPUT '+json.dumps(result,ensure_ascii=False),flush=True)
