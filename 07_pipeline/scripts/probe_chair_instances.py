"""只读检查正式课椅节点／装配，并用小型真实渲染验证集合实例自定义属性进入共享材质。"""
from pathlib import Path
import json
import sys
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wood_layers_blender import aim

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '07_pipeline/cache/chair_instances_20261001'
OUT = ROOT / '06_review/chair_instances_20261001'


def inspect():
    """输入当前正式文件，输出椅子组的链接、关键默认值与图像映射，供针对性编辑。"""
    roots = sorted([o for o in bpy.context.scene.objects if o.get('chair_asset')], key=lambda o: o.name)
    first = roots[0]
    mats = {m for o in first.children for m in o.data.materials if m}
    groups = {n.node_tree for m in mats for n in m.node_tree.nodes if n.type == 'GROUP'}
    def tree(t):
        """输入节点树，返回节点用途／接口与实际连线；输出不含打包图像像素。"""
        return {'nodes': [{'name': n.name, 'type': n.type, 'props': dict(n.items()),
            'operation': getattr(n, 'operation', None),
            'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None,
            'extension': getattr(n, 'extension', None),
            'inputs': {s.name: list(s.default_value) if hasattr(s.default_value, '__len__') else s.default_value
                for s in n.inputs if hasattr(s, 'default_value')}} for n in t.nodes],
            'links': [[l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name] for l in t.links]}
    record = {'file': bpy.data.filepath, 'roots': [o.name for o in roots],
        'groups': {g.name: tree(g) for g in groups},
        'materials': {m.name: tree(m.node_tree) for m in mats},
        'parts': [{'name': o.name, 'source': o['chair_source_part'], 'matrix': [list(r) for r in o.matrix_basis],
            'materials': [m.name for m in o.data.materials], 'vertices': len(o.data.vertices)} for o in first.children]}
    (WORK / 'inspection.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print('INSPECTED', len(roots), len(first.children), len(mats), flush=True)


def probe():
    """输入空测试场景，输出两实例的发光颜色像素差；验证共享材质读取实例属性与Int组接口。"""
    scene = bpy.data.scenes.new('PROBE / instancer attributes')
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1
    # The asset exists only through collection instances in this scene.
    asset = bpy.data.collections.new('PROBE / shared cube')
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.object
    for c in list(cube.users_collection): c.objects.unlink(cube)
    asset.objects.link(cube)
    mat = bpy.data.materials.new('PROBE / shared material'); mat.use_nodes = True
    t = mat.node_tree; t.nodes.clear()
    attr = t.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'INSTANCER'; attr.attribute_name = 'test_seed'
    g = bpy.data.node_groups.new('PROBE / Int seed', 'ShaderNodeTree')
    g.interface.new_socket(name='Seed', in_out='INPUT', socket_type='NodeSocketInt')
    g.interface.new_socket(name='Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    i = g.nodes.new('NodeGroupInput'); o = g.nodes.new('NodeGroupOutput')
    div = g.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'; div.inputs[1].default_value = 10
    g.links.new(i.outputs['Seed'], div.inputs[0]); g.links.new(div.outputs[0], o.inputs[0])
    gn = t.nodes.new('ShaderNodeGroup'); gn.node_tree = g; t.links.new(attr.outputs['Fac'], gn.inputs['Seed'])
    emission = t.nodes.new('ShaderNodeEmission'); out = t.nodes.new('ShaderNodeOutputMaterial')
    t.links.new(gn.outputs['Result'], emission.inputs['Color']); t.links.new(emission.outputs[0], out.inputs['Surface'])
    cube.data.materials.append(mat)
    for x, seed in [(-1.5, 2), (1.5, 8)]:
        ob = bpy.data.objects.new('PROBE / instance', None); scene.collection.objects.link(ob)
        ob.instance_type = 'COLLECTION'; ob.instance_collection = asset; ob.location.x = x; ob['test_seed'] = seed
    cam = bpy.data.objects.new('PROBE / camera', bpy.data.cameras.new('PROBE / camera'))
    scene.collection.objects.link(cam); cam.location = (0, -10, 0); aim(cam, (0, 0, 0))
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 7; scene.camera = cam
    scene.render.resolution_x = 210; scene.render.resolution_y = 90; scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'; scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.filepath = str(OUT / 'attribute_probe.exr')
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(str(OUT / 'attribute_probe.exr'))
    pixels = np.array(im.pixels[:], dtype=np.float32).reshape(90, 210, 4)
    values = [float(pixels[45, x, 0]) for x in [60, 150]]
    audit = {'values': values, 'expected': [.2, .8], 'passed': max(abs(v-e) for v,e in zip(values,[.2,.8])) < .01}
    (OUT / 'attribute_probe.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    assert audit['passed'], audit
    print('INSTANCE_ATTRIBUTE_PROBE', audit, flush=True)


if __name__ == '__main__':
    WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    inspect(); probe()
