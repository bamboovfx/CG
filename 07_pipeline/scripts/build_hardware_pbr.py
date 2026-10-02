"""窗五金次世代资产流程：当前源→可编辑高模/三角化低模→4K UV图集→高低模烘焙→候选。

仅处理20260927已修正的五金，不重建窗框或更改用户控制器。所有加工纹理自制；
厂商参考只决定几何/装配，不使用照片做贴图。阶段中间文件全部留在cache。
"""
import bpy
import bmesh
import math
import json
import sys
import hashlib
from pathlib import Path
from mathutils import Matrix

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
CACHE=ROOT/'07_pipeline/cache/window_hardware_pbr'
OUT=ROOT/'06_review/window_hardware_pbr'
TEX=ROOT/'02_assets/textures/window_hardware'
UV='UVMap'
SIZE=4096


def select_only(objects, active=None):
    """输入对象列表与活动项，设置明确操作上下文；不依赖原选择。"""
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objects: o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active=active or objects[0]


def signature(o):
    """输入网格对象，以局部几何和修改器尺寸分组；仅完全同形零件共享低模。"""
    data={'v':[[round(x,7) for x in v.co] for v in o.data.vertices],
          'f':[list(p.vertices) for p in o.data.polygons],
          'mods':[(m.type,round(getattr(m,'width',0),7)) for m in o.modifiers]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def material_source(kind):
    """输入制造工艺，创建米制细纹/轻微粗糙度变化；返回可用于分通道烘焙的节点材质。"""
    mat=bpy.data.materials.new('Hardware source '+kind); mat.use_nodes=True
    ns=mat.node_tree.nodes; ls=mat.node_tree.links; ns.clear()
    out=ns.new('ShaderNodeOutputMaterial'); out.location=(700,0)
    bs=ns.new('ShaderNodeBsdfPrincipled'); bs.location=(410,0); ls.new(bs.outputs[0],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(.64,.65,.66,1); bs.inputs['Metallic'].default_value=1
    tc=ns.new('ShaderNodeTexCoord'); tc.location=(-850,100)
    scale=ns.new('ShaderNodeVectorMath'); scale.operation='MULTIPLY'; scale.location=(-650,100)
    # 板件沿长轴轻度抛光，铸造锁杯/轴为均匀细哑光；高度最大约0.6微米。
    scale.inputs[1].default_value=(10000,10000,90) if kind=='sheet' else (6500,6500,6500)
    ls.new(tc.outputs['Object'],scale.inputs[0])
    grain=ns.new('ShaderNodeTexNoise'); grain.location=(-450,100); grain.inputs['Scale'].default_value=1; grain.inputs['Detail'].default_value=1
    ls.new(scale.outputs[0],grain.inputs['Vector'])
    rough=ns.new('ShaderNodeMapRange'); rough.location=(-100,150)
    rough.inputs['To Min'].default_value=.28 if kind=='sheet' else .32
    rough.inputs['To Max'].default_value=.34 if kind=='sheet' else .38
    ls.new(grain.outputs['Fac'],rough.inputs['Value']); ls.new(rough.outputs[0],bs.inputs['Roughness'])
    bump=ns.new('ShaderNodeBump'); bump.location=(150,-150); bump.inputs['Strength'].default_value=.18; bump.inputs['Distance'].default_value=.0000006
    ls.new(grain.outputs['Fac'],bump.inputs['Height']); ls.new(bump.outputs[0],bs.inputs['Normal'])
    # 内部属性用于查找；可见节点名称保持软件默认。
    bs['role']='surface'; rough['role']='roughness'; out['role']='output'
    frame=ns.new('NodeFrame'); frame.label='米制加工细纹：板件轻拉丝 / 铸件细哑光；不烘焙照明'; frame.location=(-900,420)
    return mat


def prepare():
    """输入已保存建筑源，创建分件高低模、唯一UV图集并保存准备态；输出清单。"""
    CACHE.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True); TEX.mkdir(parents=True,exist_ok=True)
    original=bpy.context.scene
    targets=[o for o in bpy.data.collections['AST_window_wall_left'].objects if o.type=='MESH' and o.get('window_hardware_20260927') and not o.name.startswith('CUT ')]
    # 槽口黑色辅助件不需要金属法线图；仍保留原形，单独记录。
    metal=[o for o in targets if 'screw slot' not in o.name]
    groups={}
    for ob in metal: groups.setdefault(signature(ob),[]).append(ob)
    scene=bpy.data.scenes.new('Hardware authoring'); bpy.context.window.scene=scene
    hc=bpy.data.collections.new('HIGH - editable bevels'); lc=bpy.data.collections.new('LOW - triangulated UV')
    scene.collection.children.link(hc); scene.collection.children.link(lc)
    mats={k:material_source(k) for k in ('sheet','cast')}
    records=[]; lows=[]
    for i,(sig,items) in enumerate(groups.items()):
        src=items[0]; key='part_%02d'%i
        high=src.copy(); high.data=src.data.copy(); high.name=key+'_high'; high.parent=None; high.matrix_world=Matrix.Translation(((i%4)*.3,(i//4)*.3,0))
        hc.objects.link(high)
        for p in high.data.polygons: p.use_smooth=True
        for m in high.modifiers:
            if m.type=='BEVEL': m.segments=6
        high['source_object']=src.name; high['purpose']='Editable high source; exploded only for matched bake'
        kind='cast' if any(t in src.name for t in ('cam','axle','screw')) else 'sheet'
        high.data.materials.clear(); high.data.materials.append(mats[kind])
        # 两段几何倒角保轮廓，六段高模与微加工纹理交给法线贴图。
        temp=high.copy(); temp.data=high.data.copy(); lc.objects.link(temp)
        for m in temp.modifiers:
            if m.type=='BEVEL': m.segments=2
        bpy.context.view_layer.update()
        me=bpy.data.meshes.new_from_object(temp.evaluated_get(bpy.context.evaluated_depsgraph_get()),preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
        low=bpy.data.objects.new(key+'_low',me); lc.objects.link(low); low.matrix_world=high.matrix_world.copy()
        bpy.data.objects.remove(temp,do_unlink=True)
        # UV在最终倒角上生成；不会再由后置倒角产生塌陷或继承拉伸。
        while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name=UV)
        select_only([low]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(32),island_margin=.003,correct_aspect=True,scale_to_bounds=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        tri=low.modifiers.new('Triangulate','TRIANGULATE'); tri.quad_method='FIXED'; tri.ngon_method='BEAUTY'
        if hasattr(tri,'keep_custom_normals'): tri.keep_custom_normals=True
        bpy.ops.object.modifier_apply(modifier=tri.name)
        low['source_object']=src.name; low['signature']=sig
        lows.append(low)
        records.append({'key':key,'high':high.name,'low':low.name,'source':src.name,'targets':[o.name for o in items],
                        'low_triangles':len(me.polygons),'process':kind})
    # 多物体一起统一密度，留20px两侧膨胀空间；禁止岛重叠。
    select_only(lows); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True,rotate_method='CARDINAL',scale=True,margin_method='FRACTION',margin=40/SIZE,merge_overlap=False,shape_method='AABB')
    bpy.ops.object.mode_set(mode='OBJECT')
    manifest={'input_sha256':hashlib.sha256((CACHE/'source_before.blend').read_bytes()).hexdigest(),
              'size':SIZE,'padding_pixels':20,'island_gap_pixels':40,'uv':UV,'groups':records,
              'targets':len(metal),'excluded_dark_slots':[o.name for o in targets if o not in metal],
              'scene':scene.name,'original_scene':original.name}
    (CACHE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'prepared.blend'),relative_remap=True)
    print('PREPARED',json.dumps({'groups':len(records),'targets':len(metal),'tris':sum(r['low_triangles'] for r in records)}))


def finish_material(images):
    """输入烘焙图集，返回仅使用UV取样的金属PBR材质；AO作为独立交付不乘进底色。"""
    mat=bpy.data.materials.new('Hardware / Satin metal baked'); mat.use_nodes=True
    ns=mat.node_tree.nodes; ls=mat.node_tree.links; ns.clear()
    uv=ns.new('ShaderNodeUVMap'); uv.uv_map=UV; uv.location=(-720,60)
    bs=ns.new('ShaderNodeBsdfPrincipled'); bs.location=(80,130)
    out=ns.new('ShaderNodeOutputMaterial'); out.location=(410,130); ls.new(bs.outputs[0],out.inputs['Surface'])
    for index,(key,socket) in enumerate([('BaseColor','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal'),('AO',None)]):
        node=ns.new('ShaderNodeTexImage'); node.image=images[key]; node.location=(-450,410-index*280); node.projection='FLAT'; node.extension='EXTEND'
        ls.new(uv.outputs['UV'],node.inputs['Vector'])
        if key=='Normal':
            nm=ns.new('ShaderNodeNormalMap'); nm.uv_map=UV; nm.location=(-100,-390); ls.new(node.outputs['Color'],nm.inputs['Color']); ls.new(nm.outputs[0],bs.inputs['Normal'])
        elif socket: ls.new(node.outputs['Color'],bs.inputs[socket])
    frame=ns.new('NodeFrame'); frame.label='4K共享UV图集 · OpenGL法线 · AO单独交付，不重复压暗底色'; frame.location=(-730,700)
    mat['pipeline']='High to low, tangent OpenGL, uniform-density UV atlas'; return mat


def bake():
    """输入准备态高低模；执行真实高→低Cycles烘焙，输出图集、独立可编辑源与建筑候选。"""
    manifest_path=CACHE/'manifest.json' if (CACHE/'manifest.json').exists() else TEX/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    scene=bpy.data.scenes[manifest['scene']]; bpy.context.window.scene=scene
    scene.view_layers[0].layer_collection.children['HIGH - editable bevels'].exclude=False
    bpy.data.collections['HIGH - editable bevels'].hide_render=False
    lows=[bpy.data.objects[r['low']] for r in manifest['groups']]; highs=[bpy.data.objects[r['high']] for r in manifest['groups']]
    # 保留各零件低模，将副本合并为一次烘焙接收体；join保留切线基与UV。
    copies=[]
    for lo in lows:
        cp=lo.copy(); cp.data=lo.data.copy(); scene.collection.objects.link(cp); copies.append(cp)
    select_only(copies); bpy.ops.object.join(); receiver=bpy.context.object; receiver.name='BAKE receiver'
    targetmat=bpy.data.materials.new('Bake target'); targetmat.use_nodes=True; targetmat.node_tree.nodes.clear()
    receiver.data.materials.clear(); receiver.data.materials.append(targetmat)
    for p in receiver.data.polygons: p.material_index=0
    target=targetmat.node_tree.nodes.new('ShaderNodeTexImage'); targetmat.node_tree.nodes.active=target
    for lo in lows: lo.hide_render=True; lo.hide_set(True)
    scene.render.engine='CYCLES'; scene.cycles.samples=32
    scene.render.bake.use_selected_to_active=True; scene.render.bake.cage_extrusion=.0009; scene.render.bake.max_ray_distance=.0018
    scene.render.bake.margin=20; scene.render.bake.margin_type='EXTEND'; scene.render.bake.normal_space='TANGENT'
    select_only(highs+[receiver],receiver)
    images={}; stats={}
    highmats={m for o in highs for m in o.data.materials if m}
    for key,bake_type in [('Normal','NORMAL'),('AO','AO'),('BaseColor','EMIT'),('Roughness','EMIT'),('Metallic','EMIT')]:
        image=bpy.data.images.new('Hardware_'+key,width=SIZE,height=SIZE,alpha=False,float_buffer=True)
        image.colorspace_settings.name='sRGB' if key=='BaseColor' else 'Non-Color'
        image.generated_color=(.5,.5,1,1) if key=='Normal' else (1,1,1,1)
        target.image=image
        for mat in highmats:
            ns=mat.node_tree.nodes; ls=mat.node_tree.links
            bs=next(n for n in ns if n.get('role')=='surface'); output=next(n for n in ns if n.get('role')=='output')
            if bake_type=='EMIT':
                emit=ns.new('ShaderNodeEmission'); emit['temporary_bake']=True
                if key=='Roughness': ls.new(next(n for n in ns if n.get('role')=='roughness').outputs[0],emit.inputs['Color'])
                else: emit.inputs['Color'].default_value=bs.inputs['Base Color'].default_value if key=='BaseColor' else (1,1,1,1)
                ls.new(emit.outputs[0],output.inputs['Surface'])
            else: ls.new(bs.outputs[0],output.inputs['Surface'])
        bpy.ops.object.bake(type=bake_type,use_selected_to_active=True,use_clear=True,margin=20,
                            cage_extrusion=.0009,max_ray_distance=.0018,normal_space='TANGENT',uv_layer=UV)
        # PNG保存使用Raw，底色由sRGB图像色彩空间编码；法线/标量保持Non-Color。
        scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
        scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'; scene.render.image_settings.color_depth='16'
        image.filepath_raw=str(TEX/(key+'.png')); image.file_format='PNG'; image.save()
        images[key]=image
        for mat in highmats:
            ns=mat.node_tree.nodes; ls=mat.node_tree.links
            for node in list(ns):
                if node.get('temporary_bake'): ns.remove(node)
            ls.new(next(n for n in ns if n.get('role')=='surface').outputs[0],next(n for n in ns if n.get('role')=='output').inputs['Surface'])
        stats[key]={'bytes':Path(image.filepath_raw).stat().st_size,'sha256':hashlib.sha256(Path(image.filepath_raw).read_bytes()).hexdigest()}
        print('BAKED',key,stats[key]['bytes'],flush=True)
    bpy.data.objects.remove(receiver,do_unlink=True)
    mat=finish_material(images)
    for lo in lows:
        lo.hide_render=False; lo.hide_set(False); lo.data.materials.clear(); lo.data.materials.append(mat)
    # 高/低分集合开关；默认显示低模。独立源无教室无关数据，方便人工继续修改。
    bpy.data.collections['HIGH - editable bevels'].hide_render=True
    scene.view_layers[0].layer_collection.children['HIGH - editable bevels'].exclude=True
    select_only(lows)
    author=ROOT/'02_assets/work/window_hardware_authoring.blend'
    bpy.data.libraries.write(str(author),{scene},path_remap='RELATIVE_ALL',fake_user=True,compress=True)
    manifest['textures']=stats; manifest['authoring']=str(author)
    (OUT/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    # 可从独立高低模源重烘焙；该模式只更新资产贴图，不假装已同步新拓扑到建筑。
    if manifest['original_scene'] not in bpy.data.scenes:
        print('AUTHORING REBAKED; geometry changes require a new reviewed geometry publish',flush=True)
        return
    # 仅替换目标mesh/material，原对象ID、父级、变换、动画和机械控制器原封保留。
    original=bpy.data.scenes[manifest['original_scene']]; bpy.context.window.scene=original
    for rec in manifest['groups']:
        data=bpy.data.objects[rec['low']].data
        for name in rec['targets']:
            ob=bpy.data.objects[name]; ob.data=data
            for mod in list(ob.modifiers): ob.modifiers.remove(mod)
            ob['hardware_pbr']='baked_20260927'; ob['editable_high_source']='//window_hardware_authoring.blend'
    # 独立authoring已写入，不把爆炸排列的工作场景混入建筑源。
    for ob in list(scene.objects): bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.scenes.remove(scene)
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'candidate.blend'),relative_remap=True)
    print('CANDIDATE',str(CACHE/'candidate.blend'),flush=True)


if __name__=='__main__':
    action=sys.argv[sys.argv.index('--')+1]
    prepare() if action=='prepare' else bake()
