"""替换被否定的低细节表现组，保留最新候选的工艺、几何、UV、五金和布光。

输入：已保存木椅候选与SD扫描辅助输出；输出：独立工程和实物尺度近景。
真实扫描色图替代常量颜色，4K沟槽／单侧纤维与浅表高度独立可调。
"""
from pathlib import Path
import sys
import json
import hashlib
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import node,socket,frame,math_node,mix,aim
from tripo_wood_reference_blender import mesh_digest
from tripo_wood_appearance_blender import process_signature

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930/tripo_wood_appearance.blend'
WORK=ROOT/'07_pipeline/cache/tripo_wood_detail_20260930'
OUT=ROOT/'06_review/tripo_wood_detail_20260930'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_detail'
PARAMS={'Scratches':.95,'Age':1.0,'Wear':.95}


def texture(tree,board,name,vector):
    """输入板和Raw图名，返回打包纹理；RGB色图用sRGB，其余是Non-Color。"""
    n=node(tree,'ShaderNodeTexImage',name)
    n.image=bpy.data.images.load(str(TEX/board/('Raw_'+name+'.png')),check_existing=True)
    n.image.colorspace_settings.name='sRGB' if name.endswith('Color') else 'Non-Color'
    n.image.pack(); n.extension='EXTEND'; tree.links.new(vector,n.inputs['Vector'])
    return n.outputs['Color']


def build_appearance(board,old):
    """输入板类型及旧组，返回多色扫描细节／污点／沟槽／掀起纤维的新组。"""
    g=bpy.data.node_groups.new('Wood / 表现层 / Scanned finish '+board,'ShaderNodeTree')
    for name,kind in [('Vector','NodeSocketVector'),('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Rear','NodeSocketFloat')]: socket(g,name,kind)
    for name,value in PARAMS.items(): socket(g,name,'NodeSocketFloat',default=value)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Coat','NodeSocketFloat'),('Coat Roughness','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input'); o=node(g,'NodeGroupOutput','output')
    signals={name:texture(g,board,name,i.outputs['Vector']) for name in ['AgeMask','AgeColor','AgeRoughness','AgeHeight','DirtMask','DirtColor','WearMask','WearColor','WearRoughness','WearHeight','ScratchCore','ScratchLip']}
    masks={name:math_node(g,'MULTIPLY',signals[name],i.outputs[param]) for name,param in [('AgeMask','Age'),('DirtMask','Age'),('WearMask','Wear'),('ScratchCore','Scratches'),('ScratchLip','Scratches')]}
    # 每个目标是完整扫描色图；真实局部颜色细节不会被三种常量棕色取代。
    c=mix(g,i.outputs['Color'],signals['AgeColor'],masks['AgeMask'],'varied_aged_finish')
    c=mix(g,c,signals['DirtColor'],math_node(g,'MULTIPLY',masks['DirtMask'],.42),'embedded_dark_marks')
    c=mix(g,c,signals['WearColor'],masks['WearMask'],'exposed_fibre_colour')
    c=mix(g,c,signals['DirtColor'],math_node(g,'MULTIPLY',masks['ScratchCore'],.77),'scratch_dark_core')
    c=mix(g,c,signals['WearColor'],masks['ScratchLip'],'scratch_lifted_fibre')
    # 保留背面印记，只读取原图，不猜测文字；正面不产生印记。
    oldstamp=next(n.image for n in old.nodes if n.type=='TEX_IMAGE' and 'StampMask' in n.image.name)
    n=node(g,'ShaderNodeTexImage','rear_stamp'); n.image=oldstamp; g.links.new(i.outputs['Vector'],n.inputs['Vector'])
    stamp=math_node(g,'MULTIPLY',n.outputs['Color'],i.outputs['Rear'])
    stamp=math_node(g,'MULTIPLY',stamp,math_node(g,'MULTIPLY',i.outputs['Age'],1.2))
    c=mix(g,c,signals['DirtColor'],stamp,'rear_stamp_preserved')
    rough=mix(g,i.outputs['Roughness'],signals['AgeRoughness'],masks['AgeMask'],'polished_and_hazed_finish')
    rough=mix(g,rough,signals['WearRoughness'],masks['WearMask'],'exposed_fibre_roughness')
    rough=mix(g,rough,signals['WearRoughness'],masks['ScratchCore'],'scratch_roughness')
    normal=i.outputs['Normal']
    heights=[(math_node(g,'MULTIPLY',math_node(g,'SUBTRACT',signals['AgeHeight'],.5),masks['AgeMask']),.00012,'scan_age_microrelief'),
             (math_node(g,'MULTIPLY',math_node(g,'SUBTRACT',signals['WearHeight'],.5),masks['WearMask']),.00022,'scan_worn_shallow_relief'),
             (math_node(g,'SUBTRACT',0,masks['ScratchCore']),.00010,'scratch_cut'),
             (masks['ScratchLip'],.00003,'lifted_fibre')]
    # 已认可法线为输入，损伤高度只在对应位置叠加；避免整块木板被粗噪声覆盖。
    for signal,distance,role in heights:
        bump=node(g,'ShaderNodeBump',role); bump.inputs['Distance'].default_value=distance; bump.inputs['Strength'].default_value=1
        g.links.new(signal,bump.inputs['Height']); g.links.new(normal,bump.inputs['Normal']); normal=bump.outputs['Normal']
    loss=math_node(g,'MAXIMUM',masks['WearMask'],masks['ScratchCore'])
    loss=math_node(g,'MAXIMUM',loss,math_node(g,'MULTIPLY',masks['AgeMask'],.30))
    coat=math_node(g,'MULTIPLY',.12,math_node(g,'SUBTRACT',1,loss))
    # 清漆保留不同粗糙度响应，涂层擦亮区可比裸木更平滑。
    coat_r=mix(g,i.outputs['Roughness'],signals['AgeRoughness'],masks['AgeMask'],'coat_local_response')
    coat_r=mix(g,coat_r,signals['WearRoughness'],masks['WearMask'],'coat_loss_response')
    for name,signal in [('Color',c),('Roughness',rough),('Normal',normal),('Coat',coat),('Coat Roughness',coat_r)]: g.links.new(signal,o.inputs[name])
    # 按依赖排版并使用注释框；所有默认节点名和标题保留。
    depths={i.name:0}; rows={}
    for _ in range(len(g.nodes)):
        for n in g.nodes:
            parents=[l.from_node.name for l in g.links if l.to_node==n]
            if n!=i and all(p in depths for p in parents): depths[n.name]=max([depths[p] for p in parents] or [0])+1
    for n in g.nodes:
        d=depths.get(n.name,0); row=rows.get(d,0); rows[d]=row+1; n.location=(d*270,row*-230)
    frame(g,'表现层：原生8K扫描→4K处理；真实多色／反射／高度，位置另控；沟槽和单侧纤维独立',[n for n in g.nodes if n not in (i,o)])
    g['detail_source']='Poly Haven wood_table_worn CC0 original 8192'; return g


def render(name,view,resolution=1400):
    """输入固定机位和尺寸，输出同光渲染；宏观／实物尺度特写分别验证。"""
    sc=bpy.context.scene; sc.camera.location=view[0]; sc.camera.data.lens=view[2]; aim(sc.camera,view[1])
    sc.render.resolution_x=resolution; sc.render.resolution_y=resolution
    sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
    print('RENDERED '+name,flush=True)


def main():
    """读取最新输入、保护摘要、替换表现组并输出工程和可审阅细节证据。"""
    OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest(); bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    sc=bpy.context.scene; prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    sc.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    sc.cycles.seed=930; sc.cycles.samples=96; sc.render.image_settings.color_depth='16'
    objects={'LP_part_02':'seat','LP_part_09':'back'}; controls={}; processes={}
    before={name:mesh_digest(bpy.data.objects[name]) for name in objects}; signatures={}
    for name,board in objects.items():
        tree=bpy.data.objects[name].data.materials[0].node_tree
        controls[board]=next(n for n in tree.nodes if n.get('wood_layers_role')=='appearance')
        processes[board]=next(n.node_tree for n in tree.nodes if n.get('wood_layers_role')=='process')
        signatures[board]=process_signature(processes[board])
    seat=((.29,-.47,.85),(0,-.035,.405),55)
    whole=((1,-1.3,.98),(0,0,.4),52)
    macro=((.035,-.335,.55),(-.095,-.145,.408),100)
    scratch_macro=((.235,-.175,.56),(.065,.025,.408),100)
    if '--seat-preview' in sys.argv:
        # 座面SD输出完成后可独立检查；不依赖正在编译的背板，也不保存半成品。
        c=controls['seat']; c.node_tree=build_appearance('seat',c.node_tree)
        for name,value in PARAMS.items(): c.inputs[name].default_value=value
        shader=next(n for n in c.id_data.nodes if n.type=='BSDF_PRINCIPLED')
        c.id_data.links.new(c.outputs['Coat Roughness'],shader.inputs['Coat Roughness'])
        render('preview_seat',seat); render('preview_contact',macro,1800); render('preview_scratch',scratch_macro,1800)
        return
    render('00_rejected_seat',seat); render('00_rejected_macro',macro,1800)
    for c in controls.values():
        for name in PARAMS: c.inputs[name].default_value=0
    render('01_process_before',seat)
    for board,c in controls.items():
        c.node_tree=build_appearance(board,c.node_tree)
        for name in PARAMS: c.inputs[name].default_value=0
        tree=c.id_data; shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
        tree.links.new(c.outputs['Coat Roughness'],shader.inputs['Coat Roughness'])
    render('02_process_after',seat)
    for c in controls.values():
        for name,value in PARAMS.items(): c.inputs[name].default_value=value
    render('03_detail_seat',seat); render('04_detail_whole',whole)
    render('05_detail_back',((.28,-.57,.81),(0,.18,.685),72))
    render('06_contact_macro',macro,1800); render('07_scratch_macro',scratch_macro,1800)
    key=next(ob for ob in sc.objects if ob.type=='LIGHT' and ob.get('wood_reference_role')=='key')
    state=(key.location.copy(),key.rotation_euler.copy(),key.data.shape,key.data.size,key.data.size_y,key.data.energy)
    key.location=(-.15,-.15,.92); key.data.shape='RECTANGLE'; key.data.size=.55; key.data.size_y=.12; key.data.energy=12; aim(key,(0,-.04,.405))
    render('08_detail_highlight',((.25,-.45,.62),(0,-.055,.405),62))
    key.location,key.rotation_euler,key.data.shape,key.data.size,key.data.size_y,key.data.energy=state
    for effect,name in [('Age','09_age_only'),('Wear','10_wear_only')]:
        for c in controls.values():
            for param,value in PARAMS.items(): c.inputs[param].default_value=value if param==effect else 0
        render(name,seat)
    for c in controls.values():
        for name,value in PARAMS.items(): c.inputs[name].default_value=value
    sc.camera.location=whole[0]; sc.camera.data.lens=whole[2]; aim(sc.camera,whole[1]); sc.render.resolution_x=sc.render.resolution_y=1400
    after={name:mesh_digest(bpy.data.objects[name]) for name in objects}
    sig_after={board:process_signature(group) for board,group in processes.items()}
    assert before==after and signatures==sig_after
    path=WORK/'tripo_wood_detail.blend'; bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(path)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(path))
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash,
        'blend':str(path.relative_to(ROOT)),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometry_before':before,'geometry_after':after,
        'process_before':signatures,'process_after':sig_after,'parameters':PARAMS,'samples':96,'macro_resolution':[1800,1800],
        'source_scan_pixels':[8192,8192],'placement_pixels':[4096,4096],'output_pixels':[4096,4096],
        'source_scan':'https://polyhaven.com/a/wood_table_worn','source_license':'CC0-1.0','visual_status':'new appearance pending user visual review'}
    assert audit['source_unchanged']; (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('WOOD_DETAIL_DONE '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
