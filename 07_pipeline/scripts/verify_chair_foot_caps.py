"""独立重开已保存胶脚分件，核对四个对象、材质、UV及实时保护摘要。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from separate_chair_foot_caps import OUT, state, geometry_digest, ID
from tripo_wood_appearance_blender import process_signature


def main():
    """输入磁盘工程，输出实际对象和依赖检查；不编辑场景或替代用户视觉评审。"""
    expected = json.loads((OUT/'expected_state.json').read_text(encoding='utf-8'))
    applied = json.loads((OUT/'applied.json').read_text(encoding='utf-8'))
    actual = state()
    # Blender重开不保留零用户且未启用Fake User的历史材质；有效资产材质仍逐一核对。
    transient = expected.get('unpersisted_materials', [])
    expected['materials'] = {k:v for k,v in expected['materials'].items() if k not in transient}
    checks = {k: actual[k] == expected[k] for k in actual}
    checks['all_saved_geometry_uv_normals'] = expected['all_geometry'] == {
        o.name: geometry_digest(o.data) for o in bpy.data.objects if o.type == 'MESH'}
    caps = list(bpy.data.collections['CHAIR / Foot caps'].objects)
    checks['four_independent_caps'] = len(caps) == 4 and {o.name for o in caps} == set(applied['caps'])
    checks['four_distinct_meshes'] = len({o.data for o in caps}) == 4
    checks['four_independent_materials'] = len({o.active_material for o in caps}) == 4
    rubber = bpy.data.materials['AITA yellowed matte foot caps']
    for ob in caps:
        checks[ob.name+'/material'] = ob.active_material.name == applied['materials'][ob.name]
        checks[ob.name+'/faces'] = len(ob.data.polygons) == applied['cap_faces'][ob.name]
        checks[ob.name+'/uv'] = [u.name for u in ob.data.uv_layers] == ['UVMap', 'UV_Material']
        checks[ob.name+'/custom_normals'] = ob.data.has_custom_normals
        checks[ob.name+'/reused_rubber'] = process_signature(ob.active_material.node_tree) == process_signature(rubber.node_tree)
    checks['temporary_ids_removed'] = not any(ID in m.attributes for m in bpy.data.meshes if m.users)
    checks['packed_images'] = all(im.packed_file for im in bpy.data.images
                                   if im.source == 'FILE' and im.users and im.size[0] > 0)
    audit = {'file': bpy.data.filepath, 'passed': all(checks.values()), 'checks': checks,
             'unpersisted_unused_materials': transient,
             'material_difference_names': [k for k in set(actual['materials']) | set(expected['materials'])
                                           if actual['materials'].get(k) != expected['materials'].get(k)],
             'caps': {o.name: {'faces':len(o.data.polygons), 'material':o.active_material.name} for o in caps}}
    (OUT/'reopen_validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    assert audit['passed'], {k:v for k,v in checks.items() if not v}
    print('FOOT_CAPS_REOPEN ' + json.dumps({'passed':True,'checks':len(checks),'caps':4}), flush=True)


if __name__ == '__main__':
    main()
