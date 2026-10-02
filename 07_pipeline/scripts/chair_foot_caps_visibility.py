"""重做胶脚表现的可见度；同光前后／归零渲染，保留工艺及实时用户编辑。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import chair_foot_caps_blender as author
from tripo_wood_appearance_blender import process_signature

ROOT=author.ROOT
WORK=ROOT/'07_pipeline/cache/chair_foot_cap_visibility_20261001'
OUT=ROOT/'06_review/chair_foot_cap_visibility_20261001'
TEX=WORK/'sd_candidate/textures'
CANDIDATE=WORK/'visibility_candidate.blend'


def replace_appearance():
    """输入当前四个胶脚和新版SD表现，输出保护审计；工艺组和原根材质保持。"""
    before=author.protected()
    factory=process_signature(bpy.data.node_groups[author.PROCESS])
    old=bpy.data.node_groups[author.APPEARANCE]
    old.name=author.APPEARANCE+' / previous'
    author.TEX=TEX
    new=author.appearance_group()
    old.user_remap(new)
    bpy.data.node_groups.remove(old)
    records=[]
    for index,ob in enumerate(bpy.data.collections['CHAIR / Foot caps'].objects):
        app=next(n for n in ob.active_material.node_tree.nodes if n.get('foot_cap_role')=='appearance')
        for k,v in author.CONTROLS.items():
            app.inputs[k].default_value=v
        app.inputs['Dirt'].default_value=[.65,.60,.70,.63][index]
        records.append({'part':ob.name,'material':ob.active_material.name,
                        'controls':{k:app.inputs[k].default_value for k in author.CONTROLS}})
    bpy.context.view_layer.update()
    assert author.protected()==before
    assert process_signature(bpy.data.node_groups[author.PROCESS])==factory
    return {'parts':records,'protected_unchanged':True,'process_signature':factory,'tile_m':.08}


def candidate():
    """输入用户实时备份，输出同光旧版／新版、整体图和真实归零对照；恢复机位再保存。"""
    OUT.mkdir(parents=True,exist_ok=True)
    author.OUT=OUT
    sc=bpy.context.scene;cam=sc.camera
    saved=(cam.location.copy(),cam.rotation_euler.copy(),cam.data.lens,
           sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
           sc.render.filepath,sc.cycles.samples,sc.cycles.seed,sc.cycles.device,
           sc.render.image_settings.color_depth,sc.cycles.use_animated_seed)
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:
        d.use=d.type=='CUDA'
    sc.cycles.device='GPU';sc.cycles.seed=101;sc.cycles.use_animated_seed=False
    sc.render.image_settings.color_depth='8'
    close=((.27,-.365,.079),(.194,-.213,-.001),90)
    author.render('before.png',close,1000,900,24)
    audit=replace_appearance()
    author.render('after.png',close,1000,900,24)
    author.render('feet.png',((.85,-1.12,.39),(0,-.025,.06),70),1280,804,24)
    materials=[]
    for record in audit['parts']:
        mat=bpy.data.materials[record['material']]
        app=next(n for n in mat.node_tree.nodes if n.get('foot_cap_role')=='appearance')
        proc=next(n for n in mat.node_tree.nodes if n.get('foot_cap_role')=='process')
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        values={k:app.inputs[k].default_value for k in author.CONTROLS}
        materials.append((mat,app,proc,shader,values))
        for k in author.CONTROLS:
            app.inputs[k].default_value=0
    author.render('zero.png',close,640,576,8)
    for mat,app,proc,shader,values in materials:
        for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
            mat.node_tree.links.new(proc.outputs[source],shader.inputs[dest])
    author.render('process.png',close,640,576,8)
    for mat,app,proc,shader,values in materials:
        for k,v in values.items():
            app.inputs[k].default_value=v
        for source,dest in [('Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
            mat.node_tree.links.new(app.outputs[source],shader.inputs[dest])
    (cam.location,cam.rotation_euler,cam.data.lens,sc.render.resolution_x,
     sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath,
     sc.cycles.samples,sc.cycles.seed,sc.cycles.device,sc.render.image_settings.color_depth,
     sc.cycles.use_animated_seed)=saved
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    (OUT/'candidate.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FOOT_CAP_VISIBILITY_CANDIDATE '+json.dumps(audit),flush=True)


if __name__=='__main__':
    candidate()
