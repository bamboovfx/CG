"""只读检查最新木椅候选；保留用户刚保存的材质、几何和布光修改。"""
from pathlib import Path
import sys
import json
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tripo_wood_reference_blender import mesh_digest
ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'07_pipeline/cache/tripo_wood_reference_20260930/tripo_wood_reference.blend'))
result = {'boards': {}, 'lights': [], 'camera': {}, 'render': {}}
for name in ('LP_part_02', 'LP_part_09'):
    ob = bpy.data.objects[name]
    mats = []
    for material in ob.data.materials:
        groups = []
        for n in material.node_tree.nodes:
            if n.type == 'GROUP':
                groups.append({'node': n.name, 'role': n.get('wood_layers_role'), 'tree': n.node_tree.name,
                    'inputs': {s.name: list(s.default_value) if hasattr(s.default_value, '__len__') else s.default_value for s in n.inputs},
                    'images': [x.image.name for x in n.node_tree.nodes if x.type == 'TEX_IMAGE']})
        mats.append({'name': material.name, 'groups': groups, 'links': [(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in material.node_tree.links]})
    # 输出投影凸包，让新版磨损贴合Tripo圆角轮廓而不是方形贴图边框。
    across = 2 if name == 'LP_part_02' else 1
    bounds = [(min(v.co[k] for v in ob.data.vertices),max(v.co[k] for v in ob.data.vertices)) for k in (0, across)]
    points = sorted(set(((v.co.x-bounds[0][0])/(bounds[0][1]-bounds[0][0]),(v.co[across]-bounds[1][0])/(bounds[1][1]-bounds[1][0])) for v in ob.data.vertices))
    def cross(a, b, c):
        """输入三个二维点，返回有向面积；用于剔除凸包内点。"""
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for sequence, half in ((points, lower),(reversed(points),upper)):
        for point in sequence:
            while len(half)>1 and cross(half[-2],half[-1],point)<=0: half.pop()
            half.append(point)
    result['boards'][name] = {'digest': mesh_digest(ob), 'materials': mats, 'uv_hull': lower[:-1]+upper[:-1]}
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type == 'LIGHT': result['lights'].append({'name': ob.name, 'role': ob.get('wood_reference_role'), 'position': list(ob.location), 'energy': ob.data.energy, 'shape': ob.data.shape})
result['camera'] = {'name': sc.camera.name, 'position': list(sc.camera.location), 'lens': sc.camera.data.lens}
result['render'] = {'engine': sc.render.engine,'samples': sc.cycles.samples,'resolution': [sc.render.resolution_x,sc.render.resolution_y], 'exposure': sc.view_settings.exposure}
out = ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930'
out.mkdir(parents=True, exist_ok=True)
(out/'input_inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('CURRENT_WOOD '+json.dumps({k:v for k,v in result.items() if k!='boards'},ensure_ascii=False),flush=True)
