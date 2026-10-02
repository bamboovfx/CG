"""独立重开检查25把可编辑课椅、逐表现种子及原场景保护，不依赖预览图替代技术验证。"""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from replace_scene_chairs import OUT, protected, layer_kind, PROPERTIES
from cleanup_wood_rear_stamp import geometry_digest
from tripo_wood_appearance_blender import process_signature


def main():
    """输入已保存工程及替换前摘要，输出几何／驱动／材质独立性和场景保护检查。"""
    expected=json.loads((OUT/'expected_state.json').read_text(encoding='utf-8'))
    # Evaluate the saved frame and drivers before comparing against the render-evaluated baseline.
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()
    actual=protected(expected['names'],expected['materials'],expected['groups'])
    checks={k:actual[k]==expected['protected'][k] for k in actual}
    differences={k:{n:{'expected':expected['protected'][k].get(n),'actual':actual[k].get(n)}
                   for n in set(actual[k])|set(expected['protected'][k]) if actual[k].get(n)!=expected['protected'][k].get(n)}
                 for k in ['objects','materials','groups']}
    (OUT/'protection_differences.json').write_text(json.dumps(differences,ensure_ascii=False,indent=2),encoding='utf-8')
    checks['original_factory_groups']={n:process_signature(bpy.data.node_groups[n]) for n in expected['factory']}==expected['factory']
    chairs=expected['chairs'];parts=[];materials=set();seeds={k:[] for k in PROPERTIES}
    normalise=Matrix(expected['normalise'])
    valid_drivers=0;appearance_nodes=0;floor_errors=[];matrix_errors=[];uv_errors=[]
    for c in chairs:
        root=bpy.data.objects[c['root']]
        checks[c['root']+'/root']=root.instance_collection is None and root.instance_type=='NONE' and [list(r) for r in root.matrix_world]==expected['placements'][root.name]
        local=[bpy.data.objects[n] for n in c['children']]
        checks[c['root']+'/29_editable_parts']=len(local)==29 and all(o.parent==root and o.type=='MESH' and o.library is None and o.data.library is None and o.data.users==1 for o in local)
        for kind,prop in PROPERTIES.items():seeds[kind].append(int(root[prop]))
        lowest=1e9
        for ob in local:
            parts.append(ob)
            src=ob['chair_source_part']
            if geometry_digest(ob.data)!=expected['part_geometry'][src]:uv_errors.append(ob.name)
            wanted=normalise@Matrix(expected['part_matrices'][src])
            error=max(abs(ob.matrix_basis[i][j]-wanted[i][j]) for i in range(4) for j in range(4))
            if error>1e-5:matrix_errors.append((ob.name,error))
            lowest=min(lowest,min((ob.matrix_basis@Vector(v)).z for v in ob.bound_box))
            for mat in ob.data.materials:
                materials.add(mat)
                assert mat.get('chair_owner')==root.name,(ob.name,mat.name)
                for n in mat.node_tree.nodes:
                    if n.type!='GROUP':continue
                    kind,offset=layer_kind(n)
                    if not kind:continue
                    appearance_nodes+=1
                    expected_seed=int(root[PROPERTIES[kind]])+offset
                    checks[ob.name+'/'+kind+'/seed']=n.inputs['Seed'].default_value==expected_seed
                    driver=next((f for f in mat.node_tree.animation_data.drivers if f.data_path==n.inputs['Seed'].path_from_id('default_value')),None)
                    if driver and driver.driver.variables[0].targets[0].id==root and driver.is_valid:valid_drivers+=1
        if abs(lowest)>1e-5:floor_errors.append((root.name,lowest))
    checks['725_independent_meshes']=len(parts)==725 and len({o.data for o in parts})==725
    checks['independent_chair_materials']=all(m.users==1 for m in materials)
    checks['original_part_geometry_uv_normals']=not uv_errors
    checks['aligned_local_matrices']=not matrix_errors
    checks['grounded_caps']=not floor_errors
    checks['four_unique_seed_sets']=all(len(set(v))==25 for v in seeds.values())
    checks['valid_seed_drivers']=valid_drivers==appearance_nodes and appearance_nodes>0
    checks['packed_chair_images']=all(n.image and n.image.packed_file for g in bpy.data.node_groups if g.get('chair_variation_seed') for n in g.nodes if n.type=='TEX_IMAGE')
    audit={'file':bpy.data.filepath,'passed':all(checks.values()),'checks':checks,'chairs':25,'parts':len(parts),
           'materials':len(materials),'appearance_nodes':appearance_nodes,'valid_drivers':valid_drivers,
           'floor_errors':floor_errors,'matrix_errors':matrix_errors,'geometry_errors':uv_errors}
    suffix='published_validation.json' if '--published' in sys.argv else 'candidate_validation.json'
    (OUT/suffix).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    assert audit['passed'],{k:v for k,v in checks.items() if not v}
    print('SCENE_CHAIRS_REOPEN '+json.dumps({k:audit[k] for k in ['passed','chairs','parts','materials','appearance_nodes','valid_drivers']}),flush=True)


if __name__=='__main__':
    main()
