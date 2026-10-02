"""从通过技术检查的独立候选追加23份分层材质到实时工作文件，仅替换对应材质槽。"""
import json
import bpy
from chair_metal_blender import CANDIDATE, CURRENT, WORK, OUT, protected


def main():
    """输入当前实时工程，保留最新编辑并备份，追加材质、核对保护项后原位保存。"""
    assert bpy.data.filepath.replace('\\', '/') == CURRENT.as_posix()
    verified = json.loads((OUT / 'candidate_reopen_validation.json').read_text(encoding='utf-8'))
    assert verified['passed']
    backup = WORK / 'pre_apply.blend'
    assert not backup.exists(), '重复应用前先检查最新工程与恢复副本'
    dirty = bpy.data.is_dirty
    before = protected()
    active = bpy.context.view_layer.objects.active
    selected = list(bpy.context.selected_objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True)
    wanted = [p['material'] for p in verified['parts']]
    assert all(name not in bpy.data.materials for name in wanted), '实时工程已经有同名材质，不能盲目追加'
    with bpy.data.libraries.load(str(CANDIDATE), link=False) as (source, dest):
        assert all(name in source.materials for name in wanted)
        dest.materials = wanted
    by_part = {m['bound_part']: m for m in dest.materials}
    for p in verified['parts']:
        ob = bpy.data.objects[p['part']]
        ob.data.materials[0] = by_part[p['part']]
    bpy.context.view_layer.update()
    assert before == protected(), '实时工程中其它材质／几何／用户位置发生改变'
    assert bpy.context.view_layer.objects.active == active and list(bpy.context.selected_objects) == selected
    outcome = bpy.ops.wm.save_as_mainfile(filepath=str(CURRENT))
    audit = {'current': str(CURRENT), 'backup': str(backup), 'source_had_unsaved_edits': dirty,
        'parts': list(by_part), 'protected_unchanged': True, 'saved': 'FINISHED' in outcome,
        'active': active.name if active else None, 'mode': bpy.context.mode}
    (OUT / 'applied.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit
