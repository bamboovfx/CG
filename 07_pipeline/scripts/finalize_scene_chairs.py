"""从保存的局部变换对齐旧椅座面，并用规范资源路径验证保护项；不忽略真实场景改动。"""
from pathlib import Path
import hashlib
import json
import sys
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from replace_scene_chairs import WORK, OUT, TARGET, CANDIDATE, protected, render
from wood_layers_blender import aim


def main():
    """baseline读取原文件的持久变换；候选合并偏置、重出实际图并保留正式渲染设置。"""
    expected=json.loads((OUT/'expected_state.json').read_text(encoding='utf-8'))
    if '--baseline' in sys.argv:
        assert Path(bpy.data.filepath)==TARGET
        assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==(WORK/'target_before.sha256').read_text().strip()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        data=protected(expected['names'],expected['materials'],expected['groups'])
        (WORK/'canonical_original_state.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print('CANONICAL_ORIGINAL_CAPTURED',flush=True)
        return
    assert Path(bpy.data.filepath)==CANDIDATE
    expected['protected']=json.loads((WORK/'canonical_original_state.json').read_text(encoding='utf-8'))
    # Old template boards have saved local offsets which an unlinked object's unevaluated world cache hides.
    old=bpy.data.objects['chair_dished_plywood_seat']
    correction=old.location.copy()
    correction.z=0  # Keep the verified foot ground datum, independently of the old seat's slight dish adjustment.
    shift=Matrix.Translation(correction)
    base=Matrix(expected.get('normalise_before_alignment',expected['normalise']))
    expected['normalise_before_alignment']=[list(r) for r in base]
    desired=shift@base
    for record in expected['chairs']:
        for name in record['children']:
            ob=bpy.data.objects[name];ob.matrix_basis=desired@Matrix(expected['part_matrices'][ob['chair_source_part']])
    expected['normalise']=[list(r) for r in desired]
    (OUT/'expected_state.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
    assert protected(expected['names'],expected['materials'],expected['groups'])==expected['protected']
    sc=bpy.context.scene
    saved=(sc.camera,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
           sc.render.filepath,sc.cycles.samples,sc.cycles.device,sc.cycles.seed,sc.render.image_settings.color_depth)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    sc.cycles.device='GPU';sc.cycles.seed=177;sc.render.image_settings.color_depth='8'
    sc.camera=bpy.data.objects['cam_sh010_main'];render('after.png',samples=16)
    review=bpy.data.objects.new('REVIEW / final chairs',bpy.data.cameras.new('REVIEW / final chairs'))
    sc.collection.objects.link(review);sc.camera=review;review.location=(.72,-3.15,1.5);aim(review,(.09,-1.38,.53));review.data.lens=48
    render('close.png',1100,900,16)
    camdata=review.data;bpy.data.objects.remove(review,do_unlink=True);bpy.data.cameras.remove(camdata)
    (sc.camera,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
     sc.render.filepath,sc.cycles.samples,sc.cycles.device,sc.cycles.seed,sc.render.image_settings.color_depth)=saved
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    print('ASSEMBLY_FINALIZED '+json.dumps({'seat_offset_correction':list(correction)}),flush=True)


if __name__=='__main__':
    main()
