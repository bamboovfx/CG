"""将已验证低模/材质合并到实时建筑源；保留对象ID、用户姿态、父级与其他材质。"""
import bpy
import sys
import json
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from validate_hardware_pbr import snapshot

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/window_hardware_pbr'
OUT=ROOT/'06_review/window_hardware_pbr'


def publish():
    """输入实时建筑源和通过验证的候选，输出已保存正式源及保护验证记录。"""
    source=ROOT/'02_assets/work/classroom_environment.blend'
    manifest=json.loads((OUT/'build_manifest.json').read_text(encoding='utf-8'))
    assert Path(bpy.data.filepath).resolve()==source.resolve(), 'Wrong Blender file'
    assert bpy.context.mode=='OBJECT', 'Please leave edit mode before geometry publish'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['input_sha256'], 'Disk source changed; rebase first'
    assert json.loads((OUT/'candidate_validation.json').read_text(encoding='utf-8'))['passed']
    before=snapshot(); baseline=json.loads((OUT/'source_fingerprint.json').read_text(encoding='utf-8'))
    assert before==baseline, 'Live source changed; preserve and rebase first'
    # 再保存临场恢复副本，防止未保存的其他属性在出现意外时丢失。
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'before_publish.blend'),copy=True,relative_remap=True)
    original_objects=set(bpy.data.objects); selected=[o.name for o in bpy.context.selected_objects]
    active=bpy.context.view_layer.objects.active; active_name=active.name if active else None
    requested=[r['targets'][0] for r in manifest['groups']]
    with bpy.data.libraries.load(str(CACHE/'candidate.blend'),link=False) as (available,loaded):
        assert all(n in available.objects for n in requested)
        loaded.objects=requested
    for rec,temp in zip(manifest['groups'],loaded.objects):
        data=temp.data
        for mat in data.materials:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    filename=Path(bpy.path.abspath(node.image.filepath)).name
                    node.image.filepath=str(ROOT/'02_assets/textures/window_hardware'/filename)
        for name in rec['targets']:
            ob=bpy.data.objects[name]; ob.data=data
            for mod in list(ob.modifiers): ob.modifiers.remove(mod)
            ob['hardware_pbr']='baked_20260928'; ob['editable_high_source']='//window_hardware_authoring.blend'
    # 仅清理由此次append创建的临时对象，既有数据不作全局purge。
    for ob in set(bpy.data.objects)-original_objects: bpy.data.objects.remove(ob,do_unlink=True)
    bpy.context.view_layer.update()
    after=snapshot(); target_names={n for r in manifest['groups'] for n in r['targets']}
    assert all(before[n]['matrix']==after[n]['matrix'] and before[n]['parent']==after[n]['parent'] for n in before)
    assert all(before[n]==after[n] for n in before if n not in target_names)
    for n in selected: bpy.data.objects[n].select_set(True)
    if active_name: bpy.context.view_layer.objects.active=bpy.data.objects[active_name]
    bpy.ops.wm.save_as_mainfile(filepath=str(source),relative_remap=True)
    result={'saved':str(source),'targets_updated':len(target_names),'transforms_preserved':True,'non_targets_preserved':True,
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    (OUT/'published.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    print(json.dumps(publish(),ensure_ascii=False))
