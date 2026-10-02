"""在用户最新木椅候选的末端追加独立表面脏渍层，保留既有工艺与表现。

输入：最新保存的候选、原生SD独立脏渍图；输出：独立工程及同光前后／归零图。
几何、UV、法线、已有组和参数不修改；表面微凸起只通过着色表达。
"""
from pathlib import Path
import sys
import hashlib
import json
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import node,socket,frame,math_node,mix,aim
from tripo_wood_reference_blender import mesh_digest
from tripo_wood_appearance_blender import process_signature

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_wood_detail_20260930/tripo_wood_detail.blend'
WORK=ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930'
OUT=ROOT/'06_review/tripo_wood_dirt_20260930'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_dirt'


def dirt_group(board):
    """输入板类型，返回独立颜色／粗糙度／法线／清漆表面污渍组。"""
    g=bpy.data.node_groups.new('Wood / 表面脏渍 / '+board,'ShaderNodeTree')
    inputs=[('Vector','NodeSocketVector'),('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Coat','NodeSocketFloat'),('Coat Roughness','NodeSocketFloat')]
    for name,kind in inputs: socket(g,name,kind)
    socket(g,'Dirt','NodeSocketFloat',default=1)
    for name,kind in inputs[1:]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-1000,0); o=node(g,'NodeGroupOutput','output',1000,0)
    signals={}
    for index,name in enumerate(['DirtMask','DirtColor','DirtRoughness','DirtHeight']):
        n=node(g,'ShaderNodeTexImage',name,-740,500-index*270)
        n.image=bpy.data.images.load(str(TEX/board/(name+'.png')),check_existing=True)
        n.image.colorspace_settings.name='sRGB' if name=='DirtColor' else 'Non-Color'
        n.image.pack(); n.extension='EXTEND'; g.links.new(i.outputs['Vector'],n.inputs['Vector'])
        signals[name]=n.outputs['Color']
    amount=math_node(g,'MULTIPLY',signals['DirtMask'],i.outputs['Dirt'],-430,450)
    # 原SD颜色仍保留多色细节；压低附着物反照率，避免亮布光下退化成淡木纹。
    tint=node(g,'ShaderNodeMixRGB','surface_dirt_colour_depth',-130,650)
    tint.blend_type='MULTIPLY'; tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.38,.44,.52,1); g.links.new(signals['DirtColor'],tint.inputs[1])
    colour=mix(g,i.outputs['Color'],tint.outputs['Color'],amount,'surface_stain_colour',0,450)
    rough=mix(g,i.outputs['Roughness'],signals['DirtRoughness'],amount,'dry_residue_roughness',0,180)
    h=math_node(g,'MULTIPLY',signals['DirtHeight'],i.outputs['Dirt'],-420,-260)
    bump=node(g,'ShaderNodeBump','surface_residue_relief',200,-200)
    bump.inputs['Distance'].default_value=.000025; bump.inputs['Strength'].default_value=1
    g.links.new(h,bump.inputs['Height']); g.links.new(i.outputs['Normal'],bump.inputs['Normal'])
    coat=math_node(g,'MULTIPLY',i.outputs['Coat'],math_node(g,'SUBTRACT',1,math_node(g,'MULTIPLY',amount,.85)),200,-480)
    coat_rough=mix(g,i.outputs['Coat Roughness'],signals['DirtRoughness'],amount,'surface_coat_response',250,-710)
    for name,signal in [('Color',colour),('Roughness',rough),('Normal',bump.outputs['Normal']),('Coat',coat),('Coat Roughness',coat_rough)]:
        g.links.new(signal,o.inputs[name])
    frame(g,'表面脏渍：细点／灰褐附着物／淡擦抹；Dirt=0恢复上一版；微凸起≤25µm',[n for n in g.nodes if n not in (i,o)])
    g['surface_dirt_layer']=True; return g


def snapshot():
    """返回两块木板的几何、工艺、表现组和控制值，用于保护用户当前修改。"""
    result={}
    for obj,board in [('LP_part_02','seat'),('LP_part_09','back')]:
        ob=bpy.data.objects[obj]; tree=ob.data.materials[0].node_tree
        proc=next(n for n in tree.nodes if n.get('wood_layers_role')=='process')
        app=next(n for n in tree.nodes if n.get('wood_layers_role')=='appearance')
        result[board]={'geometry':mesh_digest(ob),'process':process_signature(proc.node_tree),'appearance':process_signature(app.node_tree),
            'parameters':{k:app.inputs[k].default_value for k in ['Age','Wear','Scratches']}}
    return result


def render(name,view,resolution=1400):
    """输入固定机位及尺寸，写出同光透视验证图。"""
    sc=bpy.context.scene; sc.camera.location=view[0]; sc.camera.data.lens=view[2]; aim(sc.camera,view[1])
    sc.render.resolution_x=sc.render.resolution_y=resolution
    sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
    print('DIRT_RENDER '+name,flush=True)


def main():
    """以最新文件追加独立层、同光渲染、归零检查并另存；不覆写用户输入。"""
    for folder in (WORK,OUT): folder.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); before=snapshot(); sc=bpy.context.scene
    camstate=(sc.camera.location.copy(),sc.camera.rotation_euler.copy(),sc.camera.data.lens)
    renderstate=(sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath)
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    sc.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    sc.cycles.samples=128; sc.cycles.seed=930; sc.render.image_settings.color_depth='16'
    seat=((.29,-.47,.85),(0,-.035,.405),55)
    macro=((.025,-.32,.545),(-.095,-.110,.408),100)
    render('00_before_seat',seat); render('01_before_macro',macro,2000)
    controls={}
    for obj,board in [('LP_part_02','seat'),('LP_part_09','back')]:
        tree=bpy.data.objects[obj].data.materials[0].node_tree
        app=next(n for n in tree.nodes if n.get('wood_layers_role')=='appearance')
        shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
        dirt=node(tree,'ShaderNodeGroup','surface_dirt',app.location.x+330,app.location.y-560)
        dirt.node_tree=dirt_group(board); dirt.inputs['Dirt'].default_value=1; controls[board]=dirt
        uv=next(l.from_socket for l in tree.links if l.to_node==app and l.to_socket.name=='Vector')
        tree.links.new(uv,dirt.inputs['Vector'])
        # 仅在原输出与BSDF之间串接；原始组内部与全部参数保持用户当前值。
        for source,target in [('Color','Base Color'),('Roughness','Roughness'),('Normal','Normal'),('Coat','Coat Weight'),('Coat Roughness','Coat Roughness')]:
            tree.links.new(app.outputs[source],dirt.inputs[source]); tree.links.new(dirt.outputs[source],shader.inputs[target])
        tree.links.new(dirt.outputs['Normal'],shader.inputs['Coat Normal'])
        frame(tree,'表面附着脏渍，独立Dirt强度；保持工艺／老化／磨损',[dirt])
    render('02_after_seat',seat); render('03_after_macro',macro,2000)
    render('04_after_back',((.28,-.57,.81),(0,.18,.685),72))
    render('05_after_whole',((1,-1.3,.98),(0,0,.4),52))
    for c in controls.values(): c.inputs['Dirt'].default_value=0
    render('06_zero_seat',seat)
    for c in controls.values(): c.inputs['Dirt'].default_value=1
    assert before==snapshot(),'Protected model or existing groups changed'
    assert source_hash==hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'Source changed during work'
    sc.camera.location,sc.camera.rotation_euler,sc.camera.data.lens=camstate
    sc.render.resolution_x,sc.render.resolution_y,sc.render.filepath=renderstate
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.make_paths_relative(); path=WORK/'tripo_wood_dirt.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'blend':str(path.relative_to(ROOT)),
        'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'protected':before,'source_unchanged':True,
        'dirt':1,'height_distance_m':.000025,'texture_resolution':4096,'macro_resolution':2000,'samples':128,
        'visual_status':'Surface dirt added; pending user visual review'}
    (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SURFACE_DIRT_DONE '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
