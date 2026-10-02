"""只读核对当前候选的法线UV、数据颜色空间和Principled通道接线。"""
from pathlib import Path
import json
import bpy

ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'07_pipeline/cache/tripo_wood_reference_20260930/tripo_wood_reference.blend'))
result={}
for name in ('LP_part_02','LP_part_09'):
    mat=bpy.data.objects[name].data.materials[0]; t=mat.node_tree
    p=t.nodes.get('Principled BSDF'); proc=next(n.node_tree for n in t.nodes if n.get('wood_layers_role')=='process')
    # 列出真实保存连接，不用生成脚本的预期结果替代工程检查。
    result[name]={'inputs':{key:[{'node':link.from_node.name,'socket':link.from_socket.name} for link in p.inputs[key].links] for key in ('Roughness','Normal','Coat Normal','Coat Roughness')},
        'normal_map':[{'uv':n.uv_map,'strength':n.inputs['Strength'].default_value} for n in proc.nodes if n.type=='NORMAL_MAP'],
        'images':[{'name':n.image.name,'colorspace':n.image.colorspace_settings.name} for n in proc.nodes if n.type=='TEX_IMAGE']}
(ROOT/'06_review/tripo_wood_reference_20260930/shading_diagnosis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
