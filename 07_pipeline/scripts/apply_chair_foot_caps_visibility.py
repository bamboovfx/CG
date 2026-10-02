"""应用已评审胶脚表现组；保留工艺、根材质、几何UV及用户当前场景修改。"""
from pathlib import Path
import json
import shutil
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from chair_foot_caps_visibility import WORK, OUT, ROOT, CANDIDATE
from chair_foot_caps_blender import protected, PROCESS, APPEARANCE
from tripo_wood_appearance_blender import process_signature


def apply():
    """输入当前实时文件，替换胶脚共享表现组并记录独立重开所需完整保护证据。"""
    source=Path(bpy.data.filepath)
    file=str(ROOT/'07_pipeline/cache/tripo_wood_side_back_20260930/tripo_wood_side_back.blend')
    assert source in [Path(file),WORK/'pre_visibility_live.blend']
    # If the live app closes, use its captured unsaved state only while the target disk file is unchanged.
    if source!=Path(file):
        import hashlib
        assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==(WORK/'target_before.sha256').read_text().strip()
    before=protected();factory=process_signature(bpy.data.node_groups[PROCESS])
    dirty=bpy.data.is_dirty
    selected=[o.name for o in bpy.context.selected_objects]
    active=bpy.context.view_layer.objects.active
    active=active.name if active else None
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'pre_apply_live.blend'),copy=True)
    # Preserve published native content before replacing the procedural appearance recipe.
    for source,target in [(ROOT/'02_assets/materials/chair_foot_caps',WORK/'previous_sd/materials'),
                          (ROOT/'02_assets/textures/generated/chair_foot_caps',WORK/'previous_sd/textures')]:
        shutil.copytree(source,target,dirs_exist_ok=True)
    for source,target in [(WORK/'sd_candidate/materials',ROOT/'02_assets/materials/chair_foot_caps'),
                          (WORK/'sd_candidate/textures',ROOT/'02_assets/textures/generated/chair_foot_caps')]:
        for src in source.iterdir():
            if src.is_file():
                shutil.copy2(src,target/src.name)
    old=bpy.data.node_groups[APPEARANCE]
    with bpy.data.libraries.load(str(CANDIDATE),link=False) as (src,dest):
        dest.node_groups=[APPEARANCE]
    new=dest.node_groups[0]
    old.user_remap(new)
    bpy.data.node_groups.remove(old)
    new.name=APPEARANCE
    # Point packed appearance images to their published location; bytes remain candidate-verified.
    for n in new.nodes:
        if n.type=='TEX_IMAGE':
            n.image.filepath=str(ROOT/'02_assets/textures/generated/chair_foot_caps'/Path(n.image.filepath).name)
    audit=json.loads((OUT/'candidate.json').read_text(encoding='utf-8'))
    for record in audit['parts']:
        ob=bpy.data.objects[record['part']]
        assert ob.active_material.name==record['material']
        app=next(n for n in ob.active_material.node_tree.nodes if n.get('foot_cap_role')=='appearance')
        assert app.node_tree==new
        for k,v in record['controls'].items():
            app.inputs[k].default_value=v
    bpy.context.view_layer.update()
    assert protected()==before
    assert process_signature(bpy.data.node_groups[PROCESS])==factory
    assert selected==[o.name for o in bpy.context.selected_objects]
    assert active==(bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None)
    expected=protected()
    expected['unpersisted_materials']=[m.name for m in bpy.data.materials if not m.users and not m.use_fake_user]
    expected['foot_materials']={r['material']:process_signature(bpy.data.materials[r['material']].node_tree) for r in audit['parts']}
    expected['foot_groups']={n:process_signature(bpy.data.node_groups[n]) for n in [PROCESS,APPEARANCE]}
    (OUT/'expected_state.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
    audit.update(file=file,had_unsaved_edits=dirty,active=active,selected=selected,process_unchanged=True,
                 recovered_live_backup=source!=Path(file))
    (OUT/'applied.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=file)
    return {'saved':True,'file':file,'process_unchanged':True,'preserved_unsaved_edits':dirty,'caps':4}


if __name__=='__main__':
    result=apply()
