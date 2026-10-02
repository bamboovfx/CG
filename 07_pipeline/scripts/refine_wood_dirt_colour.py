"""仅压深新脏渍反照率，重渲对应评审；已有木材工艺／表现和位置不修改。"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import tripo_wood_dirt_blender as base
from wood_layers_blender import node
ROOT=Path(__file__).resolve().parents[2]; OUT=base.OUT
path=base.WORK/'tripo_wood_dirt.blend'
audit=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(path)); assert base.snapshot()==audit['protected']
sc=bpy.context.scene
camera=(sc.camera.location.copy(),sc.camera.rotation_euler.copy(),sc.camera.data.lens)
settings=(sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath)
prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
for d in prefs.devices: d.use=d.type=='OPTIX'
sc.cycles.device='GPU'
controls=[]
for obj in ['LP_part_02','LP_part_09']:
    group=next(n for n in bpy.data.objects[obj].data.materials[0].node_tree.nodes if n.get('wood_layers_role')=='surface_dirt')
    controls.append(group); g=group.node_tree
    mix=next(n for n in g.nodes if n.get('wood_layers_role')=='surface_stain_colour')
    source=next(n for n in g.nodes if n.get('wood_layers_role')=='DirtColor')
    # 保留默认节点名称，内部属性用于再次执行时复用。
    tint=next((n for n in g.nodes if n.get('wood_layers_role')=='surface_dirt_colour_depth'),None)
    if tint is None: tint=node(g,'ShaderNodeMixRGB','surface_dirt_colour_depth',-130,650)
    tint.blend_type='MULTIPLY'; tint.inputs[0].default_value=1; tint.inputs[2].default_value=(.38,.44,.52,1)
    g.links.new(source.outputs['Color'],tint.inputs[1]); g.links.new(tint.outputs['Color'],mix.inputs[2])
    tint.parent=next(n for n in g.nodes if n.type=='FRAME')
base.render('02_after_seat',((.29,-.47,.85),(0,-.035,.405),55))
base.render('03_after_macro',((.025,-.32,.545),(-.095,-.110,.408),100),2000)
base.render('04_after_back',((.28,-.57,.81),(0,.18,.685),72))
base.render('05_after_whole',((1,-1.3,.98),(0,0,.4),52))
for c in controls: c.inputs['Dirt'].default_value=0
base.render('06_zero_seat',((.29,-.47,.85),(0,-.035,.405),55))
for c in controls: c.inputs['Dirt'].default_value=1
assert base.snapshot()==audit['protected']
assert hashlib.sha256((ROOT/audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
sc.camera.location,sc.camera.rotation_euler,sc.camera.data.lens=camera
sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath=settings
bpy.context.preferences.filepaths.save_version=0; bpy.ops.wm.save_as_mainfile(filepath=str(path))
audit['dirt_colour_linear_multiplier']=[.38,.44,.52]
audit['blend_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('DIRT_COLOUR_REFINED '+audit['blend_sha256'],flush=True)
