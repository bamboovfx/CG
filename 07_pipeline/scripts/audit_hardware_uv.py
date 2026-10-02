"""只读检查窗五金实际UV与贴图取样链；返回拉伸指标和错误投影，供修正前后复验。"""
import bpy
import json
import sys
import numpy as np
from pathlib import Path


def upstream_types(socket, seen=None):
    """输入节点插口，追踪实际连线来源；输出节点类型及输出插口名。"""
    seen=set() if seen is None else seen
    rows=[]
    for link in socket.links:
        node=link.from_node
        if node.as_pointer() in seen: continue
        seen.add(node.as_pointer())
        rows.append((node.bl_idname,link.from_socket.name))
        for inp in node.inputs:
            rows.extend(upstream_types(inp,seen))
    return rows


def inspect_uv(ob):
    """对带修改器的真实三角形求UV/表面雅可比，输出退化三角形和形变分位数。"""
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=eo.to_mesh(); me.calc_loop_triangles()
    if not me.uv_layers.active:
        eo.to_mesh_clear(); return {'name':ob.name,'missing_uv':True}
    uv=me.uv_layers.active.data
    ratios=[]; densities=[]; collapsed=0; total=0
    for tri in me.loop_triangles:
        ps=[np.array(eo.matrix_world@me.vertices[i].co) for i in tri.vertices]
        a,b=ps[1]-ps[0],ps[2]-ps[0]; area=np.linalg.norm(np.cross(a,b))*.5
        if area<1e-14: continue
        total+=1
        uvs=[np.array(uv[i].uv) for i in tri.loops]
        du=np.column_stack((uvs[1]-uvs[0],uvs[2]-uvs[0]))
        e=a/np.linalg.norm(a); xx=np.dot(b,e); yy=np.sqrt(max(0,np.dot(b,b)-xx*xx))
        if yy<1e-12: continue
        jac=du@np.linalg.inv(np.array([[np.linalg.norm(a),xx],[0,yy]]))
        sv=np.linalg.svd(jac,compute_uv=False)
        if sv[1]<1e-10: collapsed+=1; continue
        ratios.append(float(sv[0]/sv[1])); densities.append(float(np.sqrt(abs(np.linalg.det(jac)))))
    result={'name':ob.name,'uv_map':me.uv_layers.active.name,'triangles':total,'collapsed':collapsed,
            'stretch_p95':float(np.percentile(ratios,95)) if ratios else None,'stretch_max':max(ratios,default=None),
            'linear_uv_density_median':float(np.median(densities)) if densities else None}
    eo.to_mesh_clear(); return result


def audit():
    """输入当前Blender场景，输出限定代表零件的UV检查和材质映射错误。"""
    names=['ARC crescent lock escutcheon.040','ARC crescent cam.040','ARC curved latch handle.040','WIN pull grip.002','ARC lock keeper.040']
    objs=[bpy.data.objects[n] for n in names]
    materials={m.name:m for o in objs for m in o.data.materials if m}
    errors=[]; chains=[]
    for name,mat in materials.items():
        if not mat.use_nodes: continue
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE':
                upstream=upstream_types(node.inputs['Vector'])
                item={'material':name,'node':node.name,'image':node.image.name if node.image else None,
                      'projection':node.projection,'upstream':upstream,'uv_box_conflict':node.projection=='BOX' and any(a=='ShaderNodeTexCoord' and b=='UV' for a,b in upstream)}
                chains.append(item)
                if item['uv_box_conflict']: errors.append(item)
    metrics=[inspect_uv(o) for o in objs]
    return {'file':bpy.data.filepath,'uv_metrics':metrics,'texture_chains':chains,'uv_box_errors':errors,
            'passed':not errors and all(not m.get('missing_uv') and m['collapsed']==0 and m['stretch_p95']<1.25 for m in metrics)}


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    report=audit()
    if args:
        p=Path(args[0]); p.parent.mkdir(exist_ok=True,parents=True); p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))
