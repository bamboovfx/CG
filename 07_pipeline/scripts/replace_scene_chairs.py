"""替换25个旧课椅实例为可编辑分件；共用工艺内容，以每椅表现Seed产生稳定轻微差异。"""
from pathlib import Path
import hashlib
import json
import math as pymath
import sys
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from chair_metal_blender import node, math, vector
from wood_layers_blender import aim, frame
from cleanup_wood_rear_stamp import geometry_digest
from tripo_wood_appearance_blender import process_signature

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'07_pipeline/cache/chair_scene_replace_20261001'
OUT=ROOT/'06_review/chair_scene_replace_20261001'
TARGET=ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
SOURCE=WORK/'approved_chair_live.blend'
CANDIDATE=WORK/'scene_chairs_candidate.blend'
OLD='AST_school_chair_HP'
PROPERTIES={'wood':'Seed Wood','dirt':'Seed Dirt','metal':'Seed Metal','feet':'Seed Feet'}


def action_state():
    """输入全部动作，返回层／通道和关键帧，验证相机与世界动画没有变化。"""
    result={}
    for a in bpy.data.actions:
        curves=[]
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:
                        curves.append({'path':c.data_path,'index':c.array_index,
                          'keys':[[list(p.co),list(p.handle_left),list(p.handle_right),p.interpolation] for p in c.keyframe_points]})
        result[a.name]=curves
    return result


def scene_signature(tree):
    """输入现有场景节点树，返回可包含未打包／未解析历史图像的保护摘要；不修订这些资产。"""
    if tree is None:return None
    records=[]
    for n in tree.nodes:
        values={s.identifier:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value
                for s in n.inputs if hasattr(s,'default_value')}
        item={'name':n.name,'type':n.bl_idname,'values':values}
        for prop in ['operation','blend_type','projection','extension','interpolation','uv_map','vector_type','convert_from','convert_to']:
            if hasattr(n,prop):item[prop]=getattr(n,prop)
        if n.type=='GROUP':item['group']=n.node_tree.name
        if n.type=='TEX_IMAGE':
            im=n.image
            path=None if im is None else (im.filepath if im.filepath.startswith('opdef:') else Path(bpy.path.abspath(im.filepath)).resolve().as_posix().casefold())
            item['image']=None if im is None else {'name':im.name,'path':path,
                'space':im.colorspace_settings.name,'packed':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None}
        records.append(item)
    links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]
    return hashlib.sha256(json.dumps({'nodes':records,'links':links},sort_keys=True,
        default=lambda value:getattr(value,'name',str(value))).encode()).hexdigest()


def protected(names=None,materials=None,groups=None):
    """输入旧场景数据名清单，返回几何／材质／场景／动画保护摘要；允许仅实例指向改变。"""
    sc=bpy.context.scene
    names=names or list(bpy.data.objects.keys())
    mats=materials or list(bpy.data.materials.keys())
    groups=groups or list(bpy.data.node_groups.keys())
    return {'objects':{n:{'matrix':[list(r) for r in Matrix.LocRotScale(bpy.data.objects[n].location,
                  bpy.data.objects[n].rotation_quaternion if bpy.data.objects[n].rotation_mode=='QUATERNION'
                  else bpy.data.objects[n].rotation_euler.to_quaternion(),bpy.data.objects[n].scale)],
                  'parent_inverse':[list(r) for r in bpy.data.objects[n].matrix_parent_inverse],
                  'parent':bpy.data.objects[n].parent.name if bpy.data.objects[n].parent else None,
                  'hidden':[bpy.data.objects[n].hide_render,bpy.data.objects[n].hide_viewport],
                  'mesh':geometry_digest(bpy.data.objects[n].data) if bpy.data.objects[n].type=='MESH' else None}
                for n in names},
       'materials':{n:scene_signature(bpy.data.materials[n].node_tree) for n in mats if bpy.data.materials[n].node_tree},
       'groups':{n:scene_signature(bpy.data.node_groups[n]) for n in groups},'actions':action_state(),
       'scene':{'camera':sc.camera.name,'frame':sc.frame_current,'range':[sc.frame_start,sc.frame_end],
          'fps':sc.render.fps,'world':sc.world.name,'world_graph':scene_signature(sc.world.node_tree),
          'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],
          'path':sc.render.filepath,'samples':sc.cycles.samples,'device':sc.cycles.device,
          'view':[sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma]}}


def layer_kind(n):
    """输入根材质组节点，返回表现所属族和板面编号；工艺及侧壁不参与Seed偏移。"""
    if n.get('foot_cap_role')=='appearance':return 'feet',0
    if n.get('chair_metal_role')=='appearance':return 'metal',0
    if n.get('wood_layers_role')=='appearance':return 'wood',1 if 'back' in n.node_tree.name else 0
    if n.get('wood_layers_role')=='surface_dirt':return 'dirt',1 if 'back' in n.node_tree.name else 0
    return None,0


def add_seed(g,kind):
    """输入共享表现组和族，公开Seed；确定性采样相位微移，只改变表现内容，不移动工艺／接触包络。"""
    assert not any(i.name=='Seed' for i in g.interface.items_tree)
    s=g.interface.new_socket(name='Seed',in_out='INPUT',socket_type='NodeSocketInt')
    s.default_value=0;s.min_value=0;s.max_value=2147483647
    inp=next(n for n in g.nodes if n.type=='GROUP_INPUT')
    links=[l for l in g.links if l.from_node==inp and l.from_socket.name=='Vector']
    amplitude=.018 if kind in ['wood','dirt'] else .075
    # Trigonometric phases are deterministic and vanish at Seed=0, preserving the approved reference.
    signals=[]
    made=set(g.nodes)
    for coefficient in [12.9898,78.233,37.719]:
        signals.append(math(g,'MULTIPLY',math(g,'SINE',math(g,'MULTIPLY',inp.outputs['Seed'],coefficient)),amplitude))
    comb=node(g,'ShaderNodeCombineXYZ','appearance_seed_phase')
    for axis,value in zip('XYZ',signals):g.links.new(value,comb.inputs[axis])
    shifted=vector(g,'ADD',inp.outputs['Vector'],comb.outputs[0])
    for l in links:
        target=l.to_socket;g.links.remove(l);g.links.new(shifted,target)
    frame(g,'Seed：仅微移表现内容采样；木UV±1.8%，金属／胶脚内容周期±7.5%；0保留原版',
          [n for n in g.nodes if n not in made])
    g['chair_variation_seed']=kind


def copy_material(original,root,cache,variant):
    """输入原材质、椅子控制对象及缓存，返回本椅独立根材质；各表现Seed驱动绑定本椅。"""
    if original in cache:return cache[original]
    mat=original.copy();mat.name=f'Chair {variant:02d} / '+original.name
    mat['chair_owner']=root.name;mat['chair_source_material']=original.name
    for n in mat.node_tree.nodes:
        if n.type!='GROUP':continue
        kind,offset=layer_kind(n)
        if not kind:continue
        seed=int(root[PROPERTIES[kind]])+offset
        n.inputs['Seed'].default_value=seed
        fc=n.inputs['Seed'].driver_add('default_value')
        var=fc.driver.variables.new();var.name='seed';var.type='SINGLE_PROP'
        var.targets[0].id=root;var.targets[0].data_path='["'+PROPERTIES[kind]+'"]'
        fc.driver.expression='seed + '+str(offset)
        # Preserve the look; small independent strength differences avoid every chair sharing identical damage depth.
        tweak=1+.025*pymath.sin(seed*.73)
        for k in ['Age','Wear','Scratches','Dirt','Rust']:
            if k in n.inputs and not n.inputs[k].is_linked:
                n.inputs[k].default_value=max(0,min(1,n.inputs[k].default_value*tweak))
    cache[original]=mat
    return mat


def replace():
    """输入最新正式场景和通过的分件，输出替换审计；保持旧控制对象矩阵与其它资产。"""
    old=bpy.data.collections[OLD]
    # Keep the unplaced previous asset as recoverable authoring data after its instance users disappear.
    old.use_fake_user=True
    roots=sorted([o for o in bpy.context.scene.objects if o.instance_collection==old],key=lambda o:o.name)
    assert len(roots)==25
    names=list(bpy.data.objects.keys());mats=list(bpy.data.materials.keys());groups=list(bpy.data.node_groups.keys())
    before=protected(names,mats,groups)
    placements={o.name:[list(r) for r in o.matrix_world] for o in roots}
    oldseat=bpy.data.objects['chair_dished_plywood_seat']
    oldmatrix=Matrix.LocRotScale(oldseat.location,oldseat.rotation_euler.to_quaternion(),oldseat.scale)
    oldpts=[oldmatrix@Vector(v) for v in oldseat.bound_box]
    oldcenter=Vector([(min(p[i] for p in oldpts)+max(p[i] for p in oldpts))/2 for i in range(3)])
    with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
        dst.collections=['LP / editable UV candidate']
    source=dst.collections[0];parts=list(source.all_objects)
    assert len(parts)==29 and all(o.type=='MESH' for o in parts)
    # Unlinked library objects can report an unevaluated identity matrix_world. Use the approved live audit,
    # and cross-check saved local transforms before constructing the assembly in this scene.
    source_audit=json.loads((WORK/'source_inspect.json').read_text(encoding='utf-8'))
    assembly={r['name']:Matrix(r['matrix']) for r in source_audit['parts']}
    for ob in parts:
        assert ob.parent is None
        saved_local=Matrix.LocRotScale(ob.location,ob.rotation_euler.to_quaternion(),ob.scale)
        assert max(abs(saved_local[i][j]-assembly[ob.name][i][j]) for i in range(4) for j in range(4))<1e-5,ob.name
    digests={o.name:geometry_digest(o.data) for o in parts}
    seat=next(o for o in parts if o.name=='LP_part_02')
    points=[assembly[seat.name]@Vector(v) for v in seat.bound_box]
    center=Vector([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
    bottom=min((assembly[o.name]@Vector(v)).z for o in parts for v in o.bound_box)
    translation=Vector((oldcenter.x+center.x,oldcenter.y+center.y,-bottom))
    normalise=Matrix.Translation(translation)@Matrix.Rotation(pymath.pi,4,'Z')
    process_groups={n.node_tree for o in parts for mat in o.data.materials for n in mat.node_tree.nodes
                    if n.type=='GROUP' and (n.get('wood_layers_role')=='process' or n.get('chair_metal_role')=='process')}
    factory={g.name:process_signature(g) for g in process_groups}
    appearances={}
    for ob in parts:
        for mat in ob.data.materials:
            for n in mat.node_tree.nodes:
                if n.type=='GROUP':
                    kind,_=layer_kind(n)
                    if kind:appearances[n.node_tree]=kind
    for g,kind in appearances.items():add_seed(g,kind)
    records=[]
    for index,root in enumerate(roots,1):
        root.instance_collection=None;root.instance_type='NONE'
        root['chair_asset']='Approved Tripo / editable parts'
        for offset,(kind,prop) in enumerate(PROPERTIES.items()):
            root[prop]=1000+index*7+offset*101
            root.id_properties_ui(prop).update(min=0,max=2147483000,description='本椅'+kind+'表现种子；改变仅影响表现内容，工艺保持')
        c=bpy.data.collections.new(f'CHAIR {index:02d} / Editable parts')
        bpy.data.collections['prp_desks'].children.link(c)
        cache={};children=[]
        for part in parts:
            ob=part.copy();ob.data=part.data.copy();ob.name=f'Chair {index:02d} / '+part.name
            ob['chair_source_part']=part.name;ob['chair_owner']=root.name
            ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4)
            ob.matrix_basis=normalise@assembly[part.name]
            ob.hide_render=False;ob.hide_viewport=False
            c.objects.link(ob)
            for slot in ob.material_slots:slot.material=copy_material(slot.material,root,cache,index)
            children.append(ob.name)
        records.append({'root':root.name,'collection':c.name,'children':children,
                        'seeds':{p:int(root[p]) for p in PROPERTIES.values()}})
    bpy.context.view_layer.update()
    assert before==protected(names,mats,groups)
    assert placements=={o.name:[list(r) for r in o.matrix_world] for o in roots}
    assert factory=={g.name:process_signature(g) for g in process_groups}
    # Unlinked imported masters are authoring references; only placed local copies enter the scene.
    source.use_fake_user=True
    expected={'protected':before,'names':names,'materials':mats,'groups':groups,
              'factory':factory,'part_geometry':digests,'placements':placements,
              'normalise':[list(r) for r in normalise],
              'part_matrices':{o.name:[list(r) for r in assembly[o.name]] for o in parts},'chairs':records}
    (OUT/'expected_state.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'chairs':records,'count':len(roots),'parts_per_chair':len(parts),'protected_unchanged':True,
            'normalise_translation':list(translation),'shared_factory_groups':list(factory),
            'appearance_groups':{g.name:k for g,k in appearances.items()},'source':str(SOURCE)}


def render(name,width=1280,height=540,samples=16):
    """输入评审名和尺寸，用原场景真实灯光渲染；不把预览设置留在正式工程。"""
    sc=bpy.context.scene;sc.render.resolution_x=width;sc.render.resolution_y=height
    sc.render.resolution_percentage=100;sc.cycles.samples=samples
    sc.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)


def candidate():
    """输入当前场景磁盘文件，输出实际替换前后／近景及恢复原设置的可编辑候选。"""
    OUT.mkdir(parents=True,exist_ok=True)
    sc=bpy.context.scene
    saved=(sc.camera,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
           sc.render.filepath,sc.cycles.samples,sc.cycles.device,sc.cycles.seed,sc.render.image_settings.color_depth)
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'pre_replace_shot.blend'),copy=True)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    sc.cycles.device='GPU';sc.cycles.seed=177;sc.render.image_settings.color_depth='8'
    # Review the chairs through the saved classroom shot camera; restore the user's corridor camera afterward.
    sc.camera=bpy.data.objects.get('cam_sh010_main',saved[0])
    if '--reuse-before' not in sys.argv:render('before.png',samples=12)
    # Restore original render state for the replacement's protection record, then resume preview settings.
    (sc.camera,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
     sc.render.filepath,sc.cycles.samples,sc.cycles.device,sc.cycles.seed,sc.render.image_settings.color_depth)=saved
    audit=replace()
    sc.cycles.device='GPU';sc.cycles.seed=177;sc.render.image_settings.color_depth='8'
    sc.camera=bpy.data.objects.get('cam_sh010_main',saved[0])
    render('after.png',samples=16)
    review=bpy.data.objects.new('REVIEW / chairs',bpy.data.cameras.new('REVIEW / chairs'))
    sc.collection.objects.link(review);sc.camera=review
    review.location=(.72,-3.15,1.5);aim(review,(.09,-1.38,.53));review.data.lens=48
    render('close.png',1100,900,24)
    data=review.data;bpy.data.objects.remove(review,do_unlink=True);bpy.data.cameras.remove(data)
    (sc.camera,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,
     sc.render.filepath,sc.cycles.samples,sc.cycles.device,sc.cycles.seed,sc.render.image_settings.color_depth)=saved
    bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))
    (OUT/'candidate.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CHAIR_SCENE_CANDIDATE '+json.dumps({'chairs':audit['count'],'parts':audit['parts_per_chair'],'protected':True}),flush=True)


if __name__=='__main__':
    candidate()
