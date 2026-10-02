"""重开本轮Blender候选并验证木材节点、依赖与保存参数。

输入：wood_layers_studio.blend，原生SD清单及当前镜头。
输出：实际读回验证JSON；不修改任何工程。
"""
from pathlib import Path
import hashlib
import json
import bpy

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/wood_layers_20260930'


def main():
    """读取保存后的候选，检查两块木板、五通道、蒙版控制和原镜头哈希；返回无。"""
    blend=ROOT/'07_pipeline/cache/wood_layers_20260930/wood_layers_studio.blend'
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    previous=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'02_assets/textures/generated/wood_layers/manifest.json').read_text(encoding='utf-8'))
    controls=[]
    for name in previous['wood_objects']:
        ob=bpy.data.objects[name]; mat=ob.data.materials[0]
        app=next(n for n in mat.node_tree.nodes if n.get('wood_layers_role')=='appearance')
        controls.append({'object':name,'material':mat.name,'parameters':{key:app.inputs[key].default_value for key in previous['parameters']}})
    missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
    checks={'two_wood_objects':len(controls)==2,'three_area_lights':sum(o.type=='LIGHT' and o.data.type=='AREA' for o in bpy.context.scene.objects)==3,'perspective_camera':bpy.context.scene.camera.data.type=='PERSP','images_resolved':not missing,'wood_metallic_zero':all(f['extrema']==[0,0] or f['extrema']==(0,0) for f in manifest['files'] if Path(f['path']).stem in {'Metallic','Process_Metallic'}),'surface_ao_white':all(f['mean_normalized']==1 for f in manifest['files'] if Path(f['path']).stem in {'AO','Process_AO'}),'source_unchanged':hashlib.sha256((ROOT/previous['input']).read_bytes()).hexdigest()==previous['input_sha256'],'controls_preserved':all(all(abs(item['parameters'][k]-v)<1e-6 for k,v in previous['parameters'].items()) for item in controls),'renders_exist':all((ROOT/p).is_file() for p in previous['renders'])}
    audit={'checks':checks,'passed':all(checks.values()),'controls':controls,'missing':missing,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'image_count':len(bpy.data.images),'source_sha256':previous['input_sha256']}
    (OUT/'reopen_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
    if not audit['passed']: raise RuntimeError('Saved material candidate did not pass read-back checks')


if __name__=='__main__':
    main()
