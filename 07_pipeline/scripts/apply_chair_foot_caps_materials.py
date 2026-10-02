"""将已评审候选的四个胶脚材质写入实时文件；保存最新用户编辑并保护其它资产。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from chair_foot_caps_blender import OUT, WORK, CANDIDATE, protected, PROCESS, APPEARANCE
from tripo_wood_appearance_blender import process_signature


def apply():
    """输入当前实时工程和候选材质，返回原位保存证据；不替换几何或场景设置。"""
    target=str(WORK.parent/'tripo_wood_side_back_20260930/tripo_wood_side_back.blend')
    assert Path(bpy.data.filepath)==Path(target),bpy.data.filepath
    assert bpy.context.mode=='OBJECT'
    before=protected()
    dirty=bpy.data.is_dirty
    selected=[o.name for o in bpy.context.selected_objects]
    active=bpy.context.view_layer.objects.active
    active=active.name if active else None
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'pre_apply_live.blend'),copy=True)
    audit=json.loads((OUT/'candidate.json').read_text(encoding='utf-8'))
    names=[r['material'] for r in audit['parts']]
    assert all(n not in bpy.data.materials for n in names)
    with bpy.data.libraries.load(str(CANDIDATE),link=False) as (source,dest):
        assert set(names)<=set(source.materials)
        # Blender loads datablocks in place; retain a separate immutable name list for verification.
        dest.materials=list(names)
    for record in audit['parts']:
        ob=bpy.data.objects[record['part']]
        assert len(ob.data.materials)==1
        mat=bpy.data.materials[record['material']]
        assert mat.get('foot_cap_bound_part')==ob.name
        ob.data.materials[0]=mat
    bpy.context.view_layer.update()
    assert protected()==before,'其它材质、几何、UV或变换变化'
    assert [o.name for o in bpy.context.selected_objects]==selected
    assert (bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None)==active
    expected=protected()
    expected['unpersisted_materials']=[m.name for m in bpy.data.materials if not m.users and not m.use_fake_user]
    expected['foot_materials']={n:process_signature(bpy.data.materials[n].node_tree) for n in names}
    expected['foot_groups']={n:process_signature(bpy.data.node_groups[n]) for n in [PROCESS,APPEARANCE]}
    (OUT/'expected_state.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=target)
    audit.update(file=target,had_unsaved_edits=dirty,active=active,selected=selected,protected_unchanged=True)
    (OUT/'applied.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'saved':True,'file':target,'caps':len(names),'protected_unchanged':True,'preserved_unsaved_edits':dirty}


if __name__=='__main__':
    result=apply()
