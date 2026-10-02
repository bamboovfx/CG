"""只读复现侧边条带与背面矩形来源；检查实际使用路径及侧壁投影退化。

输入：用户最新保存木椅；输出：可重复、能报告两种症状的诊断JSON。
不修改材质、UV、几何或当前DCC。--require-clean用于修复后检验。
"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_side_back_20260930'; OUT.mkdir(parents=True,exist_ok=True)


def inspect(ob,thickness):
    """输入木板及局部厚度轴，返回侧壁实际着色、UV退化和背面印记连接证据。"""
    m=ob.data; m.calc_loop_triangles(); uv=m.uv_layers['UV_WoodReference']; edge=m.materials[1].node_tree
    planar_degenerate=0; side_triangles=0; broad_bevels=0
    for tri in m.loop_triangles:
        if m.polygons[tri.polygon_index].material_index!=1:
            if .52<abs(tri.normal[thickness])<.9: broad_bevels+=1
            continue
        side_triangles+=1
        a,b,c=[np.array(uv.data[l].uv) for l in tri.loops]
        if abs(float(np.linalg.det(np.stack([b-a,c-a]))))<1e-9: planar_degenerate+=1
    coord=[n for n in edge.nodes if n.type=='TEX_COORD']
    separate=[n for n in edge.nodes if n.type=='SEPXYZ']
    sin=[n for n in edge.nodes if n.type=='MATH' and n.operation=='SINE']
    one_axis_bands=bool(coord and separate and sin and not any(n.type in {'TEX_NOISE','TEX_IMAGE','TEX_VORONOI'} for n in edge.nodes))
    app=next(n for n in m.materials[0].node_tree.nodes if n.get('wood_layers_role')=='appearance')
    stamp=[n for n in app.node_tree.nodes if n.type=='TEX_IMAGE' and 'StampMask' in n.image.name]
    # 明确矩形是否仍接入颜色：旧路径用rear_stamp_preserved混合，检查其Factor控制。
    mix=next((n for n in app.node_tree.nodes if n.get('wood_layers_role')=='rear_stamp_preserved'),None)
    stamp_active=bool(stamp and mix and mix.inputs[0].is_linked)
    return {'object':ob.name,'edge_material':m.materials[1].name,'side_triangles':side_triangles,
        'broad_bevels_using_face_projection':broad_bevels,'projected_side_uv_collapses':planar_degenerate,
        'side_material_reads_uv':any(n.type=='UVMAP' for n in edge.nodes),'side_material_uses_only_thickness_sine':one_axis_bands,
        'legacy_rectangular_stamp_connected_to_colour':stamp_active,'stamp_images':[n.image.name for n in stamp]}


records={board:inspect(bpy.data.objects[obj],axis) for obj,board,axis in [('LP_part_02','seat',1),('LP_part_09','back',2)]}
symptoms={'uniform_thickness_bands':any(v['side_material_uses_only_thickness_sine'] for v in records.values()),
    'back_rectangular_stamp':records['back']['legacy_rectangular_stamp_connected_to_colour']}
result={'filepath':bpy.data.filepath,'boards':records,'symptoms':symptoms,'clean':not any(symptoms.values())}
filename='probe_after.json' if '--require-clean' in sys.argv else 'probe_before.json'
(OUT/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('SIDE_BACK_PROBE '+json.dumps(result,ensure_ascii=False),flush=True)
if '--require-clean' in sys.argv: assert result['clean'],symptoms
