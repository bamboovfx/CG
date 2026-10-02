"""在最新Tripo木椅候选中只加强表现层，另存并作同光前后验证。

输入：用户最近保存的木椅候选、独立SD蒙版；输出：可调新版及对照渲染。
工艺节点、原图、几何、UV和五金均保留；损伤是着色凹凸，不改变轮廓。
"""
from pathlib import Path
import sys
import hashlib
import json
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import node,socket,frame,math_node,mix,aim
from tripo_wood_reference_blender import color,mesh_digest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_wood_reference_20260930/tripo_wood_reference.blend'
WORK=ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930'
OUT=ROOT/'06_review/tripo_wood_appearance_20260930'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_appearance'
PARAMS={'Scratches':.95,'Age':.72,'Wear':.88}


def texture(tree,board,name,vector):
    """输入组、板、Raw技术图名和UV，返回打包且Non-Color的纹理输出。"""
    n=node(tree,'ShaderNodeTexImage',name)
    n.image=bpy.data.images.load(str(TEX/board/('Raw_'+name+'.png')),check_existing=True)
    n.image.colorspace_settings.name='Non-Color'; n.image.pack(); n.extension='EXTEND'
    tree.links.new(vector,n.inputs['Vector']); return n.outputs['Color']


def tint(tree,source,value,operation,role):
    """输入颜色、线性系数与颜色运算，返回保留木纹的着色变化。"""
    n=node(tree,'ShaderNodeMixRGB',role); n.blend_type=operation; n.inputs[0].default_value=1
    tree.links.new(source,n.inputs[1]); n.inputs[2].default_value=value
    return n.outputs[0]


def appearance(board,old):
    """输入板类型与旧组，返回独立老化／磨损／划痕组；旧背面印记保留。"""
    g=bpy.data.node_groups.new('Wood / 表现层 / Finish damage '+board,'ShaderNodeTree')
    for name,kind in [('Vector','NodeSocketVector'),('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Rear','NodeSocketFloat')]: socket(g,name,kind)
    for name,value in PARAMS.items(): socket(g,name,'NodeSocketFloat',default=value)
    for name,kind in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Normal','NodeSocketVector'),('Coat','NodeSocketFloat')]: socket(g,name,kind,'OUTPUT')
    i=node(g,'NodeGroupInput','input',-1700,0); o=node(g,'NodeGroupOutput','output',2400,0)
    masks={}
    for name in ('AgeBleach','AgeDark','AgeLoss','AgeRelief','WearMask','WearRelief','ScratchDark','ScratchLight'):
        p='Age' if name.startswith('Age') else 'Wear' if name.startswith('Wear') else 'Scratches'
        masks[name]=math_node(g,'MULTIPLY',texture(g,board,name,i.outputs['Vector']),i.outputs[p])
    # 局部失色与发暗都保留原木纹细节；不是覆盖一块平色油漆。
    pale=tint(g,i.outputs['Color'],(.70,.86,1.15,1),'MULTIPLY','faded_tint')
    pale=tint(g,pale,(.070,.062,.042,1),'ADD','faded_lift')
    dark=tint(g,i.outputs['Color'],(.46,.42,.31,1),'MULTIPLY','oxidised_tint')
    c=mix(g,i.outputs['Color'],dark,masks['AgeDark'],'aged_amber')
    c=mix(g,c,pale,masks['AgeBleach'],'finish_faded')
    mono=node(g,'ShaderNodeRGBToBW','exposed_grain'); g.links.new(i.outputs['Color'],mono.inputs[0])
    bare=tint(g,mono.outputs[0],(.10,.10,.10,1),'MULTIPLY','exposed_grain_scale')
    bare=tint(g,bare,color((.58,.44,.27)),'ADD','exposed_fibre_colour')
    c=mix(g,c,bare,masks['WearMask'],'contact_worn_wood')
    c=mix(g,c,color((.20,.085,.025)),masks['ScratchDark'],'dark_scratch')
    c=mix(g,c,color((.72,.58,.34)),masks['ScratchLight'],'pale_scratch')
    # 继承旧组的真实印记资源，不重新猜测文字或改变正反面限制。
    oldstamp=next(n.image for n in old.nodes if n.type=='TEX_IMAGE' and 'StampMask' in n.image.name)
    stamp=node(g,'ShaderNodeTexImage','rear_stamp'); stamp.image=oldstamp
    g.links.new(i.outputs['Vector'],stamp.inputs['Vector'])
    stampmask=math_node(g,'MULTIPLY',stamp.outputs['Color'],i.outputs['Rear'])
    stampmask=math_node(g,'MULTIPLY',stampmask,math_node(g,'MULTIPLY',i.outputs['Age'],1.2))
    c=mix(g,c,color((.18,.08,.025)),stampmask,'rear_imprint')
    scratch=math_node(g,'MAXIMUM',masks['ScratchDark'],masks['ScratchLight'])
    loss=math_node(g,'MAXIMUM',masks['AgeLoss'],masks['WearMask'])
    rough=mix(g,i.outputs['Roughness'],.51,masks['AgeBleach'],'faded_finish_rough')
    rough=mix(g,rough,.63,masks['AgeLoss'],'damaged_finish_rough')
    rough=mix(g,rough,.74,masks['WearMask'],'bare_fibre_rough')
    rough=mix(g,rough,.66,scratch,'scratch_rough')
    normal=i.outputs['Normal']
    # 凹槽物理高度分别为120/220/100微米；完整涂层区域仍保持原法线。
    for signal,distance,role in [(masks['AgeRelief'],.00012,'age_coating_loss'),(masks['WearRelief'],.00022,'worn_fibre_relief'),(scratch,.00010,'scratch_groove')]:
        b=node(g,'ShaderNodeBump',role); b.inputs['Distance'].default_value=distance; b.inputs['Strength'].default_value=1
        g.links.new(math_node(g,'SUBTRACT',0,signal),b.inputs['Height']); g.links.new(normal,b.inputs['Normal'])
        normal=b.outputs['Normal']
    coat=math_node(g,'MULTIPLY',.12,math_node(g,'SUBTRACT',1,math_node(g,'MAXIMUM',loss,scratch)))
    for name,signal in [('Color',c),('Roughness',rough),('Normal',normal),('Coat',coat)]: g.links.new(signal,o.inputs[name])
    # 自动按依赖层次布置默认节点，说明集中在注释框里。
    depths={i.name:0}
    for _ in range(len(g.nodes)):
        for n in g.nodes:
            incoming=[l.from_node.name for l in g.links if l.to_node==n]
            if n!=i and all(name in depths for name in incoming): depths[n.name]=max([depths[name] for name in incoming] or [0])+1
    rows={}
    for n in g.nodes:
        if n in (i,o): continue
        d=depths.get(n.name,1); row=rows.get(d,0); rows[d]=row+1
        n.location=(-1400+d*260,700-row*250)
    o.location=(max(depths.values())*260-1000,0)
    frame(g,'表现层：发暗／褪色／涂层破损，真实圆角与接触区露木；浅表凹槽120／220／100µm',[n for n in g.nodes if n not in (i,o)])
    g['appearance_revision']='20260930_contact_finish_damage'; return g


def process_signature(group):
    """输入工艺组，返回节点、接线和打包图像摘要，检验工艺层未被重制。"""
    nodes=[]
    for n in group.nodes:
        values={s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value')}
        item={'name':n.name,'type':n.bl_idname,'values':values}
        if n.type=='TEX_IMAGE': item.update(image=n.image.name,packed=hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest(),space=n.image.colorspace_settings.name)
        if n.type=='NORMAL_MAP': item.update(uv=n.uv_map,strength=n.inputs['Strength'].default_value)
        nodes.append(item)
    data={'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in group.links]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def render(name,location,target,lens):
    """输入评审名与机位，固定原布光和色彩管理，输出PNG供同光比较。"""
    sc=bpy.context.scene; sc.camera.location=location; sc.camera.data.lens=lens; aim(sc.camera,target)
    sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
    print('RENDERED '+name,flush=True)


def main():
    """保护最新输入，只替换表现组，保存并记录几何／工艺／原文件保护证据。"""
    OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); sc=bpy.context.scene
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    sc.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    sc.cycles.seed=930; sc.render.image_settings.color_depth='16'
    boards={'LP_part_02':'seat','LP_part_09':'back'}
    geom_before={name:mesh_digest(bpy.data.objects[name]) for name in boards}
    controls={}; processes={}; signatures={}; oldparams={}
    for obj,board in boards.items():
        tree=bpy.data.objects[obj].data.materials[0].node_tree
        controls[board]=next(n for n in tree.nodes if n.get('wood_layers_role')=='appearance')
        processes[board]=next(n.node_tree for n in tree.nodes if n.get('wood_layers_role')=='process')
        signatures[board]=process_signature(processes[board])
        oldparams[board]={name:controls[board].inputs[name].default_value for name in PARAMS}
    seat=((.29,-.47,.85),(0,-.035,.405),55)
    whole=((1,-1.3,.98),(0,0,.4),52)
    key=next(ob for ob in sc.objects if ob.type=='LIGHT' and ob.get('wood_reference_role')=='key')
    key_state=(key.location.copy(),key.rotation_euler.copy(),key.data.shape,key.data.size,key.data.size_y,key.data.energy)
    render('00_before_seat',*seat)
    # 诊断条形光降低功率，避免过曝盖住损伤处的反射变化。
    key.location=(-.15,-.15,.92); key.data.shape='RECTANGLE'; key.data.size=.55; key.data.size_y=.12; key.data.energy=12; aim(key,(0,-.04,.405))
    render('00_before_highlight',(.25,-.45,.62),(0,-.055,.405),62)
    key.location,key.rotation_euler,key.data.shape,key.data.size,key.data.size_y,key.data.energy=key_state
    # 归零图用于证明工艺层和着色基线一致。
    for control in controls.values():
        for name in PARAMS: control.inputs[name].default_value=0
    render('01_process_before',*seat)
    for board,control in controls.items():
        control.node_tree=appearance(board,control.node_tree)
        for name,value in PARAMS.items(): control.inputs[name].default_value=0
    render('02_process_after',*seat)
    for control in controls.values():
        for name,value in PARAMS.items(): control.inputs[name].default_value=value
    render('03_after_seat',*seat); render('04_after_whole',*whole)
    render('05_after_back',(.28,-.57,.81),(0,.18,.685),72)
    key.location=(-.15,-.15,.92); key.data.shape='RECTANGLE'; key.data.size=.55; key.data.size_y=.12; key.data.energy=12; aim(key,(0,-.04,.405))
    render('06_after_highlight',(.25,-.45,.62),(0,-.055,.405),62)
    key.location,key.rotation_euler,key.data.shape,key.data.size,key.data.size_y,key.data.energy=key_state
    # 隔离同机位的老化和磨损，检验各自有可见色差和局部反射损伤。
    for effect,name in [('Age','07_age_only'),('Wear','08_wear_only')]:
        for control in controls.values():
            for param,value in PARAMS.items(): control.inputs[param].default_value=value if param==effect else 0
        render(name,*seat)
    for control in controls.values():
        for name,value in PARAMS.items(): control.inputs[name].default_value=value
    # 恢复原工作室机位，保存用户可继续编辑的独立工程。
    sc.camera.location=whole[0]; sc.camera.data.lens=whole[2]; aim(sc.camera,whole[1])
    geom_after={name:mesh_digest(bpy.data.objects[name]) for name in boards}
    signatures_after={board:process_signature(g) for board,g in processes.items()}
    assert geom_before==geom_after and signatures==signatures_after
    bpy.context.preferences.filepaths.save_version=0
    path=WORK/'tripo_wood_appearance.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path)); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(path))
    audit={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash,
        'blend':str(path.relative_to(ROOT)),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometry_before':geom_before,'geometry_after':geom_after,
        'process_before':signatures,'process_after':signatures_after,'parameters':PARAMS,'previous_parameters':oldparams,
        'appearance_height_m':{'age':.00012,'wear':.00022,'scratch':.00010},'visual_status':'user accepted process direction; revised appearance pending visual review'}
    assert audit['source_unchanged']
    (OUT/'validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('APPEARANCE_DONE '+json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
