"""Final calibrated wear layer: keep local SD chips but reduce raw-wood exposure in a still-serviceable classroom."""
import bpy
from pathlib import Path
R=Path('D:/00_projects/10_CG/Shot_Test')
for mat in bpy.data.materials:
    if not mat.use_nodes or mat.get('sd_family')!='teaching_varnished_wood':continue
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    for n in list(nodes):
        if n.type!='TEX_IMAGE' or not n.image or 'WearMask' not in n.image.name:continue
        targets=[l.to_socket for l in links if l.from_node==n]
        scale=nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=.30
        links.new(n.outputs[0],scale.inputs[0])
        for socket in targets:links.new(scale.outputs[0],socket)
    mat['edge_wear_mix']=.30
bpy.ops.wm.save_as_mainfile(filepath=str(R/'02_assets/work/classroom_teaching.blend'))
