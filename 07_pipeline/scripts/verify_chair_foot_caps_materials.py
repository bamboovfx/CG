"""独立重开检查胶脚分层材质、打包4K贴图以及实时场景的几何／UV保护摘要。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from chair_foot_caps_blender import OUT, protected, PROCESS, APPEARANCE
from tripo_wood_appearance_blender import process_signature


def main():
    """输入磁盘工程和实时保存证据，输出通道接线、独立控制和保护项检查。"""
    expected=json.loads((OUT/'expected_state.json').read_text(encoding='utf-8'))
    applied=json.loads((OUT/'applied.json').read_text(encoding='utf-8'))
    expected['materials']={k:v for k,v in expected['materials'].items() if k not in expected['unpersisted_materials']}
    actual=protected()
    checks={k:actual[k]==expected[k] for k in actual}
    caps=list(bpy.data.collections['CHAIR / Foot caps'].objects)
    checks['four_independent_caps']=len(caps)==4 and len({o.data for o in caps})==4
    checks['four_independent_materials']=len({o.active_material for o in caps})==4
    for record in applied['parts']:
        ob=bpy.data.objects[record['part']];mat=ob.active_material;tree=mat.node_tree
        app=next(n for n in tree.nodes if n.get('foot_cap_role')=='appearance')
        proc=next(n for n in tree.nodes if n.get('foot_cap_role')=='process')
        shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
        prefix=ob.name+'/'
        checks[prefix+'bound_material']=mat.name==record['material'] and mat.get('foot_cap_bound_part')==ob.name and mat.users==1
        checks[prefix+'saved_graph']=process_signature(tree)==expected['foot_materials'][mat.name]
        checks[prefix+'uv_normals']=[u.name for u in ob.data.uv_layers]==['UVMap','UV_Material'] and ob.data.has_custom_normals
        checks[prefix+'two_layers']=proc.node_tree.name==PROCESS and app.node_tree.name==APPEARANCE
        checks[prefix+'polymer']=shader.inputs['Coat Weight'].default_value==0 and abs(shader.inputs['IOR'].default_value-1.46)<1e-6
        checks[prefix+'local_coordinates']=any(n.type=='TEX_COORD' and n.object is None for n in tree.nodes)
        for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
            checks[prefix+dest]=any(l.from_node==app and l.from_socket.name==source and l.to_node==shader and l.to_socket.name==dest for l in tree.links)
        checks[prefix+'appearance_controls']=all(0<app.inputs[k].default_value<1 for k in ['Age','Wear','Scratches','Dirt'])
    images=set()
    for name in [PROCESS,APPEARANCE]:
        g=bpy.data.node_groups[name]
        checks[name+'/saved_graph']=process_signature(g)==expected['foot_groups'][name]
        images.update(n.image for n in g.nodes if n.type=='TEX_IMAGE')
    checks['nine_packed_4k_contents']=len(images)==9 and all(im.packed_file and tuple(im.size)==(4096,4096) for im in images)
    checks['color_spaces']=all(im.colorspace_settings.name==('sRGB' if 'Color' in Path(im.filepath).stem else 'Non-Color') for im in images)
    out=next(n for n in bpy.data.node_groups[PROCESS].nodes if n.type=='GROUP_OUTPUT')
    checks['nonmetal_ao']=out.inputs['Metallic'].default_value==0 and out.inputs['AO'].default_value==1
    audit={'file':bpy.data.filepath,'passed':all(checks.values()),'checks':checks,'packed_images':len(images)}
    (OUT/'reopen_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    assert audit['passed'],{k:v for k,v in checks.items() if not v}
    print('FOOT_CAP_MATERIALS_REOPEN '+json.dumps({'passed':True,'checks':len(checks)}),flush=True)


if __name__=='__main__':
    main()
