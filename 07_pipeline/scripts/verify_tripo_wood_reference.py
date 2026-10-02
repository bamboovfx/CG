"""读回分层Tripo候选，检查材质绑定、几何保护、通道和可解析依赖。"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_reference_blender import mesh_digest, ROOT, SOURCE, WORK, OUT, TEX, PARAMS


def main():
    """读回已保存工程和输入哈希，输出客观技术验证；不代替视觉评审。"""
    path=WORK/'tripo_wood_reference.blend'; bpy.ops.wm.open_mainfile(filepath=str(path))
    audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    boards={name:mesh_digest(bpy.data.objects[name]) for name in ('LP_part_02','LP_part_09')}
    controls={}
    shader_checks={}
    for name in boards:
        mat=bpy.data.objects[name].data.materials[0]
        app=next(n for n in mat.node_tree.nodes if n.get('wood_layers_role')=='appearance')
        controls[name]={k:app.inputs[k].default_value for k in PARAMS}
        shader=mat.node_tree.nodes.get('Principled BSDF')
        proc=next(n.node_tree for n in mat.node_tree.nodes if n.get('wood_layers_role')=='process')
        shader_checks[name]={'roughness_connected':shader.inputs['Roughness'].is_linked,'normal_connected':shader.inputs['Normal'].is_linked,
            'coat_normal_connected':shader.inputs['Coat Normal'].is_linked,'coat_roughness_connected':shader.inputs['Coat Roughness'].is_linked,
            'normal_uv_correct':all(n.uv_map=='UV_WoodReference' for n in proc.nodes if n.type=='NORMAL_MAP'),
            'data_non_color':all(n.image.colorspace_settings.name=='Non-Color' for n in proc.nodes if n.type=='TEX_IMAGE' and 'BaseColor' not in n.image.name)}
    images=[im for im in bpy.data.images if im.source=='FILE' and im.users]
    missing=[im.filepath for im in images if not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
    checks={'tripo_parts':len([o for o in bpy.context.scene.objects if o.name.startswith('LP_part_')])==26,
        'correct_seat_binding':bpy.data.objects['LP_part_02'].data.materials[0].get('wood_reference_board')=='seat',
        'correct_back_binding':bpy.data.objects['LP_part_09'].data.materials[0].get('wood_reference_board')=='back',
        'geometry_uv_normals_preserved':boards==audit['board_geometry_before'],
        'controls_saved':all(abs(v[k]-PARAMS[k])<1e-5 for v in controls.values() for k in PARAMS),
        'source_preserved':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==audit['source_sha256'],
        'images_resolved':not missing,'three_area_lights':len([o for o in bpy.context.scene.objects if o.type=='LIGHT' and o.data.type=='AREA'])==3,
        'perspective':bpy.context.scene.camera.data.type=='PERSP',
        'all_renders':all((OUT/name).is_file() for name in audit['renders'])}
    checks['shader_connections']=all(all(values.values()) for values in shader_checks.values())
    for board in ('seat','back'):
        im=bpy.data.images.load(str(TEX/board/'Metallic.png'),check_existing=True)
        checks[board+'_metallic_zero']=max(im.pixels[:3])==0
    result={'checks':checks,'passed':all(checks.values()),'missing_images':missing,'image_count':len(images),'controls':controls,'shader_checks':shader_checks,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (OUT/'reopen_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False)); assert result['passed'],result


if __name__=='__main__': main()
