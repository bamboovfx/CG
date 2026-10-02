"""重开金属候选或工作文件，核对实际接线、打包图、保护项与绑定；不修改场景。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chair_metal_blender import OUT, PARTS, geometry_digest, process_signature


def main():
    """输入实际打开的Blender文件，输出结构／依赖检查，并返回各部件的真实控制值。"""
    reference = json.loads((OUT / 'validation.json').read_text(encoding='utf-8'))
    boards = ['LP_part_02', 'LP_part_09']
    checks = {}; parts = []; material_names = set()
    names = PARTS + reference['fastener_parts']
    checks['all_23_metal_parts_bound'] = all(bpy.data.objects[name].data.materials[0].get('chair_metal_layers') for name in names)
    checks['all_original_geometry_uv_normals'] = all(geometry_digest(bpy.data.objects[name].data) == digest
        for name, digest in reference['original_protected']['geometry'].items())
    # 只检查仍在使用的木材与胶脚；旧金属材质已由恢复副本完整保存。
    old = reference['original_protected']['materials']
    wood = [m for m in bpy.data.materials if m.name.startswith(('Reference wood /', 'Wood / side cross-section /'))]
    checks['wood_root_materials_unchanged'] = all(process_signature(m.node_tree) == old[m.name] for m in wood)
    checks['wood_groups_unchanged'] = all(process_signature(g) == old[g.name] for g in bpy.data.node_groups
        if not g.name.startswith('Chair metal /'))
    checks['rubber_foot_cap_unchanged'] = process_signature(bpy.data.materials['AITA yellowed matte foot caps'].node_tree) == old['AITA yellowed matte foot caps']
    checks['stamp_stays_removed'] = not any(m.attributes.get('reference_rear') for m in bpy.data.meshes) and not any('StampMask' in im.name for im in bpy.data.images)
    for name in names:
        ob = bpy.data.objects[name]; mat = ob.data.materials[0]; material_names.add(mat.name)
        tree = mat.node_tree
        proc = next(n for n in tree.nodes if n.get('chair_metal_role') == 'process')
        app = next(n for n in tree.nodes if n.get('chair_metal_role') == 'appearance')
        shader = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
        checks[name + '/local_bound_mapping'] = mat.get('bound_part') == name and any(n.type == 'TEX_COORD' for n in tree.nodes)
        checks[name + '/channels'] = all(any(l.from_node == app for l in shader.inputs[socket].links)
            for socket in ['Base Color', 'Roughness', 'Metallic', 'Normal', 'Coat Normal', 'Coat Weight', 'Coat Roughness'])
        parts.append({'part': name, 'material': mat.name, 'process': proc.node_tree.name,
            'appearance': app.node_tree.name, 'controls': {k: app.inputs[k].default_value for k in reference['controls']}})
    images = {n.image for g in bpy.data.node_groups if g.name.startswith('Chair metal /')
        for n in g.nodes if n.type == 'TEX_IMAGE' and n.image}
    checks['12_used_images_packed_4k'] = len(images) == 12 and all(im.packed_file and tuple(im.size) == (4096, 4096) for im in images)
    # Process_Normal作为SD导出保留；三向映射在Blender用物理高度生成法线，实际用12图。
    checks['colour_spaces'] = all(im.colorspace_settings.name == ('sRGB' if 'Color' in Path(im.filepath).stem else 'Non-Color') for im in images)
    passed = all(checks.values())
    audit = {'filepath': bpy.data.filepath, 'passed': passed, 'checks': checks, 'parts': parts,
        'image_count': len(images), 'material_count': len(material_names)}
    label = 'current' if 'tripo_wood_side_back' in bpy.data.filepath else 'candidate'
    (OUT / (label + '_reopen_validation.json')).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    assert passed, {k: v for k, v in checks.items() if not v}
    print('CHAIR_METAL_REOPEN ' + json.dumps({'label': label, 'checks': len(checks), 'passed': passed}), flush=True)


if __name__ == '__main__':
    main()
