"""Author finite, component-specific desk wear and verify the current native asset."""
import hashlib
import json
import math
import os
import shutil
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / '07_pipeline/cache/desk_regional_wear_20261006'
SOURCE = ROOT / '02_assets/work/school_desk.blend'
INPUT = WORK / 'input.blend'
TARGET = WORK / 'candidate.blend'
METAL = 'KOKUYO / Grey painted steel'
CAPS = 'KOKUYO / Grey molded foot caps'
VIEWS = [('full',-40,17,(0,0,.335),2.30,70),
         ('brace',-55,19,(-.195,-.08,.155),.65,85),
         ('leg',-48,13,(-.249,-.155,.30),.68,78),
         ('tray',-22,5,(0,-.02,.585),.98,75),
         ('hook',-78,12,(-.265,.006,.602),.30,72),
         ('cap',-45,13,(-.249,-.161,.041),.24,72)]


def digest(path):
    """Return streaming file SHA256 for source reconciliation and dependencies."""
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()


def fingerprint():
    """Fingerprint meshes, every UV, transforms, normals, modifiers and material assignments."""
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH': continue
        m=o.data
        data={'matrix':list(map(list,o.matrix_world)),
              'v':[list(v.co) for v in m.vertices],
              'p':[list(p.vertices) for p in m.polygons],
              'smooth':[p.use_smooth for p in m.polygons],
              'material':[p.material_index for p in m.polygons],
              'slots':[s.material.name if s.material else None for s in o.material_slots],
              'uv':{u.name:[list(v.uv) for v in u.data] for u in m.uv_layers},
              'normals':[list(n.vector) for n in m.corner_normals],
              'modifiers':[(q.name,q.type,q.show_render,q.show_viewport) for q in o.modifiers]}
        result[o.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    return result


def graph_signature(tree):
    """Serialize persistent wood shader inputs, connections and packed source identity recursively."""
    rows=[]
    for n in tree.nodes:
        row={'name':n.name,'type':n.bl_idname,'inputs':[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]}
        for key in ['operation','blend_type','projection','extension','interpolation','uv_map']:
            if hasattr(n,key):row[key]=str(getattr(n,key))
        if n.type=='GROUP':row['group']=graph_signature(n.node_tree)
        if n.type=='TEX_IMAGE' and n.image:
            im=n.image;row['image']=[im.name,list(im.size),im.colorspace_settings.name,hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None]
        rows.append(row)
    return {'nodes':rows,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]}


def protected_other():
    """Protect wood, geometry AO and all native camera/world/controls state from material-only authoring."""
    trees={name:graph_signature(bpy.data.materials[name].node_tree) for name in ['KOKUYO / Wood veneer and clearcoat','KOKUYO / Plywood edge']}
    ao=images_by_role(bpy.data.materials[METAL])['AO']
    camera=bpy.context.scene.camera
    data={'wood':trees,'ao':hashlib.sha256(ao.packed_file.data).hexdigest(),
          'camera':[camera.name,list(map(list,camera.matrix_world)),camera.data.lens],
          'world':graph_signature(bpy.context.scene.world.node_tree),
          'object_state':{o.name:[o.hide_render,o.hide_viewport,list(o.color),{k:str(o[k]) for k in o.keys()}] for o in bpy.data.objects}}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def baseline_extra():
    """Add dependency and protected shader hashes before source mutation or final-map replacement."""
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    path=WORK/'baseline.json';data=json.loads(path.read_text(encoding='utf-8'))
    assert digest(SOURCE)==data['sha256']
    data['protected_other']=protected_other()
    data['dependencies']={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'02_assets/textures/generated/kokuyo_desk').rglob('*.png')}
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGIONAL_BASELINE_EXTRA_OK',len(data['dependencies']),flush=True)


def setup():
    """Configure temporary matching studio light and detected GPU, preserving native source settings."""
    sc=bpy.context.scene
    sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True
    sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.015
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        sc.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    except Exception:sc.cycles.device='CPU'
    for name,pos,power,size in [('Key',(1,-1.4,1.9),60,1),('Fill',(-1.2,-.3,1.3),34,.85),('Rim',(.2,1.1,1.4),48,.65)]:
        o=bpy.data.objects.get(name)
        if o and o.type=='LIGHT':
            o.location=pos;o.data.energy=power;o.data.size=size
            o.rotation_euler=(Vector((0,0,.45))-o.location).to_track_quat('-Z','Y').to_euler()
    if sc.world and sc.world.use_nodes:
        bg=next((n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'),None)
        if bg:bg.inputs['Color'].default_value=(.16,.16,.16,1);bg.inputs['Strength'].default_value=.4
    sc.camera.data.type='PERSP';sc.camera.data.clip_start=.01


def render_view(view,label,resolution=1600):
    """Render an actual native-size-texture desk view to a temporary inspection PNG."""
    name,yaw,el,target,distance,lens=view
    camera=bpy.context.scene.camera;center=Vector(target)
    yaw,el=math.radians(yaw),math.radians(el)
    camera.location=center+Vector((math.sin(yaw)*math.cos(el),-math.cos(yaw)*math.cos(el),math.sin(el)))*distance
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
    sc=bpy.context.scene;sc.render.resolution_x=resolution;sc.render.resolution_y=int(resolution*.8);sc.render.resolution_percentage=100
    sc.render.filepath=str(WORK/f'{label}_{name}.png')
    print('REGIONAL_RENDER',label,name,flush=True);bpy.ops.render.render(write_still=True)


def inspect():
    """Read the preserved source, list real bounds/mappings and render the current appearance."""
    WORK.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    rows=[]
    for o in bpy.data.objects:
        if o.get('model_role')!='LOW':continue
        points=[o.matrix_world@v.co for v in o.data.vertices]
        rows.append({'name':o.name,'category':list(o.color),'materials':[m.name for m in o.data.materials],
                     'uv':[u.name for u in o.data.uv_layers],
                     'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]})
    baseline={'sha256':digest(SOURCE),'protected':fingerprint(),'parts':rows,
              'images':[{'name':i.name,'path':i.filepath,'size':list(i.size),'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE']}
    (WORK/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGIONAL_PARTS',json.dumps(rows,ensure_ascii=False),flush=True)
    setup()
    for view in VIEWS:render_view(view,'before')


def node(tree,kind,role=None):
    """Create a default-named Blender node; custom properties identify its authoring role."""
    n=tree.nodes.new(kind)
    if role:n['region_role']=role
    return n


def link(tree,value,socket):
    """Assign a literal or connect one shader signal to an input socket."""
    if hasattr(value,'node'):tree.links.new(value,socket)
    else:socket.default_value=value


def calc(tree,operation,a,b=None,c=None):
    """Return one scalar mathematical signal from constants or connected sockets."""
    n=node(tree,'ShaderNodeMath');n.operation=operation
    for i,v in enumerate([a,b,c]):
        if v is not None:link(tree,v,n.inputs[i])
    return n.outputs[0]


def smooth(tree,value,lo,hi):
    """Return a cubic smoothstep with explicit physical-domain boundaries."""
    u=calc(tree,'DIVIDE',calc(tree,'SUBTRACT',value,lo),hi-lo)
    u=calc(tree,'MINIMUM',1,calc(tree,'MAXIMUM',0,u))
    return calc(tree,'MULTIPLY',calc(tree,'MULTIPLY',u,u),calc(tree,'SUBTRACT',3,calc(tree,'MULTIPLY',2,u)))


def mix(tree,a,b,amount):
    """Blend scalar or color shader values by a shared phase mask."""
    n=node(tree,'ShaderNodeMixRGB');n.blend_type='MIX'
    link(tree,amount,n.inputs[0])
    for value,socket in [(a,n.inputs[1]),(b,n.inputs[2])]:
        if isinstance(value,(int,float)):value=(value,value,value,1)
        link(tree,value,socket)
    return n.outputs[0]


def vector(tree,x,y,z=0):
    """Return a composed 3D coordinate from scalar inputs."""
    n=node(tree,'ShaderNodeCombineXYZ')
    for v,s in zip([x,y,z],n.inputs):link(tree,v,s)
    return n.outputs[0]


def noise(tree,position,scale,detail=2):
    """Return isotropic manufacturing grain in metres, independent of finite wear marks."""
    n=node(tree,'ShaderNodeTexNoise');link(tree,position,n.inputs['Vector'])
    n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail
    return n.outputs['Fac']


def atlas_coords(tree,u,v,col,row):
    """Map one finite event into its atlas cell with an inset that excludes generated divider seams."""
    u=calc(tree,'MINIMUM',.995,calc(tree,'MAXIMUM',.005,u))
    v=calc(tree,'MINIMUM',.995,calc(tree,'MAXIMUM',.005,v))
    return vector(tree,calc(tree,'ADD',calc(tree,'MULTIPLY',col,.25),calc(tree,'ADD',.016,calc(tree,'MULTIPLY',u,.218))),
                       calc(tree,'ADD',(3-row)*.25,calc(tree,'ADD',.016,calc(tree,'MULTIPLY',v,.218))))


def texture_signals(tree,coord,images):
    """Sample registered imagegen channels once per finite projection, with no repeating extension."""
    result={}
    for channel,im in images.items():
        n=node(tree,'ShaderNodeTexImage');n.image=im;n.extension='EXTEND';n.interpolation='Linear'
        link(tree,coord,n.inputs['Vector']);result[channel]=n.outputs['Color']
    return result


def source_image(tree,filename,coord,data=False):
    """Read one nonrepeating generated full-component source at explicit physical coordinates."""
    im=bpy.data.images.load(str(WORK/filename),check_existing=True)
    im.colorspace_settings.name='Non-Color' if data else 'sRGB'
    n=node(tree,'ShaderNodeTexImage');n.image=im;n.extension='EXTEND'
    link(tree,coord,n.inputs['Vector']);return n.outputs['Color']


def luma(tree,value):
    """Return linear luminance of a registered source color without modifying source pixels."""
    n=node(tree,'ShaderNodeRGBToBW');link(tree,value,n.inputs[0]);return n.outputs[0]


def within(tree,value,center,radius,fade=.15):
    """Return a finite smooth strip gate around a measured centre and half-width."""
    d=calc(tree,'ABSOLUTE',calc(tree,'SUBTRACT',value,center))
    return calc(tree,'SUBTRACT',1,smooth(tree,d,radius*(1-fade),radius))


def metal_author(material):
    """Project distinct finite wear onto tube crowns, legs, sheet contacts and hardware bends."""
    old_images=images_by_role(material)
    t=material.node_tree;t.nodes.clear()
    shader=node(t,'ShaderNodeBsdfPrincipled','shader');out=node(t,'ShaderNodeOutputMaterial','output')
    link(t,shader.outputs[0],out.inputs['Surface'])
    geo=node(t,'ShaderNodeNewGeometry')
    p=node(t,'ShaderNodeSeparateXYZ');n=node(t,'ShaderNodeSeparateXYZ')
    link(t,geo.outputs['Position'],p.inputs[0]);link(t,geo.outputs['Normal'],n.inputs[0])
    x,y,z=p.outputs;nx,ny,nz=n.outputs
    side=calc(t,'GREATER_THAN',x,0)
    front=calc(t,'LESS_THAN',y,0)
    attr=node(t,'ShaderNodeAttribute');attr.attribute_name='MetalCategory'
    categories=[calc(t,'COMPARE',attr.outputs['Fac'],v,.04) for v in [0,.25,.5,.75,1]]
    images={}
    for channel in ['BaseColor','Metallic','Roughness','Height']:
        im=bpy.data.images.load(str(WORK/f'{channel}.png'),check_existing=True)
        im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';images[channel]=im
    # Four full-height strips occur once each, keeping submillimetre chips free of periodic bands.
    col=calc(t,'ADD',side,calc(t,'MULTIPLY',front,2))
    v=calc(t,'DIVIDE',calc(t,'SUBTRACT',z,.0335),.620)
    angle=calc(t,'ARCTAN2',ny,nx)
    u=calc(t,'ADD',.5,calc(t,'DIVIDE',angle,math.tau))
    leg_coord=vector(t,calc(t,'ADD',calc(t,'MULTIPLY',col,.25),calc(t,'ADD',.012,calc(t,'MULTIPLY',u,.226))),calc(t,'ADD',.012,calc(t,'MULTIPLY',v,.976)))
    leg_color=source_image(t,'Leg_BaseColor.png',leg_coord)
    leg_phase=smooth(t,source_image(t,'Leg_Phase.png',leg_coord,True),.10,.80)
    # Existing imagegen microchips keep their actual millimetre scale; unique long-strip fields
    # change the regional density and add fragmented impacts, avoiding large generated blobs.
    old_uv=node(t,'ShaderNodeUVMap');old_uv.uv_map='UV_MetalPBR'
    old=texture_signals(t,old_uv.outputs[0],{c:old_images[c] for c in ['BaseColor','Metallic']})
    fragment=smooth(t,noise(t,geo.outputs['Position'],1150,2),.39,.62)
    impact=calc(t,'MULTIPLY',leg_phase,calc(t,'MULTIPLY',fragment,.68))
    density=calc(t,'ADD',.38,calc(t,'MULTIPLY',noise(t,geo.outputs['Position'],13,3),.45))
    density=calc(t,'ADD',density,calc(t,'MULTIPLY',leg_phase,.22))
    fine=calc(t,'MULTIPLY',smooth(t,old['Metallic'],.035,.33),density)
    leg_color=mix(t,leg_color,old['BaseColor'],smooth(t,fine,.035,.15))
    leg_phase=calc(t,'MAXIMUM',fine,impact)
    leg_core=smooth(t,luma(t,leg_color),.055,.18)
    leg_maps={'BaseColor':leg_color,'Metallic':mix(t,.16,.84,leg_core),
              'Roughness':mix(t,.68,.46,leg_core),'Height':calc(t,'SUBTRACT',.5,calc(t,'MULTIPLY',leg_phase,.13))}
    lower=smooth(t,calc(t,'SUBTRACT',.46,z),.0,.32)
    leg_gate=calc(t,'MULTIPLY',smooth(t,z,.03,.045),calc(t,'ADD',.82,calc(t,'MULTIPLY',lower,.18)))
    # Unfold the three-sided footrest path; unique corridors stay on its upper crown.
    left=calc(t,'LESS_THAN',x,-.235);right=calc(t,'GREATER_THAN',x,.235)
    on_side=calc(t,'MULTIPLY',calc(t,'MAXIMUM',left,right),calc(t,'LESS_THAN',y,.135))
    left_s=calc(t,'ADD',y,.141)
    right_s=calc(t,'SUBTRACT',1.06,calc(t,'ADD',y,.141))
    path=mix(t,calc(t,'ADD',.281,calc(t,'ADD',x,.249)),mix(t,left_s,right_s,right),on_side)
    # MixRGB scalar output is converted by Math inputs; resulting path is continuous around bends.
    length=calc(t,'DIVIDE',path,.265)
    segment=calc(t,'MINIMUM',3,calc(t,'MAXIMUM',0,calc(t,'FLOOR',length)))
    along=calc(t,'SUBTRACT',length,segment)
    across_n=mix(t,ny,nx,on_side)
    around=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'ARCTAN2',across_n,nz),math.tau))
    brace_coord=vector(t,calc(t,'ADD',.005,calc(t,'MULTIPLY',along,.99)),
                       calc(t,'ADD',calc(t,'MULTIPLY',calc(t,'SUBTRACT',3,segment),.25),calc(t,'ADD',.012,calc(t,'MULTIPLY',around,.226))))
    brace_color=source_image(t,'Brace_BaseColor.png',brace_coord)
    brace_phase=calc(t,'SUBTRACT',1,smooth(t,luma(t,brace_color),.24,.41))
    brace_core=smooth(t,luma(t,brace_color),.06,.16)
    brace_maps={'BaseColor':brace_color,'Metallic':mix(t,.22,.92,brace_core),
                'Roughness':mix(t,.64,.32,brace_core),'Height':calc(t,'SUBTRACT',.5,calc(t,'MULTIPLY',brace_phase,.13))}
    brace_gate=smooth(t,nz,-.08,.26)
    # The sheet floor receives three limited 200 mm book slides, rather than tube-like mottling.
    lane=calc(t,'ADD',calc(t,'GREATER_THAN',x,-.07),calc(t,'GREATER_THAN',x,.07))
    lane_center=calc(t,'MULTIPLY',calc(t,'SUBTRACT',lane,1),.145)
    u=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'ADD',y,.015),.20))
    v=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'SUBTRACT',x,lane_center),.068))
    slide_col=calc(t,'ADD',calc(t,'MULTIPLY',calc(t,'GREATER_THAN',lane,.5),2),calc(t,'GREATER_THAN',lane,1.5))
    slides=texture_signals(t,atlas_coords(t,u,v,slide_col,2),images)
    slide_gate=calc(t,'MULTIPLY',within(t,x,lane_center,.034),within(t,y,-.015,.10))
    slide_gate=calc(t,'MULTIPLY',slide_gate,smooth(t,nz,.45,.86))
    # Four mouth contacts and two folded corners have local chip silhouettes and unequal severity.
    mouth_index=calc(t,'MINIMUM',3,calc(t,'MAXIMUM',0,calc(t,'FLOOR',calc(t,'DIVIDE',calc(t,'ADD',x,.24),.12))))
    mouth_center=calc(t,'ADD',-.18,calc(t,'MULTIPLY',mouth_index,.12))
    u=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'SUBTRACT',x,mouth_center),.11))
    v=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'ARCTAN2',nz,calc(t,'MULTIPLY',ny,-1)),math.tau))
    lips=texture_signals(t,atlas_coords(t,u,v,1,2),images)
    lip_gate=calc(t,'MULTIPLY',within(t,y,-.164,.009),within(t,z,.567,.016))
    lip_gate=calc(t,'MULTIPLY',lip_gate,calc(t,'ADD',.55,calc(t,'MULTIPLY',noise(t,geo.outputs['Position'],22),.45)))
    tray_maps={c:mix(t,slides[c],lips[c],lip_gate) for c in images}
    tray_gate=calc(t,'MAXIMUM',slide_gate,lip_gate)
    # Hook wear is localized to load-bearing lower arcs and outward-facing wire, upper stems remain painted.
    hook_col=calc(t,'MODULO',calc(t,'ADD',side,front),2)
    u=calc(t,'SUBTRACT',.5,calc(t,'DIVIDE',calc(t,'SUBTRACT',calc(t,'ABSOLUTE',x),.267),.035))
    v=calc(t,'DIVIDE',calc(t,'SUBTRACT',z,.576),.035)
    hooks=texture_signals(t,atlas_coords(t,u,v,hook_col,3),images)
    hook_low=calc(t,'SUBTRACT',1,smooth(t,z,.591,.611))
    hook_face=smooth(t,calc(t,'ABSOLUTE',nx),.12,.65)
    hook_gate=calc(t,'MULTIPLY',hook_low,hook_face)
    # Sparse plate corner events, deliberately quieter than the touched frame and hooks.
    u=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'SUBTRACT',calc(t,'ABSOLUTE',y),.111),.036))
    v=calc(t,'ADD',.5,calc(t,'DIVIDE',calc(t,'SUBTRACT',z,.576),.027))
    mounts=texture_signals(t,atlas_coords(t,u,v,calc(t,'ADD',2,side),3),images)
    mount_gate=smooth(t,calc(t,'ABSOLUTE',y),.068,.105)
    sets=[leg_maps,brace_maps,tray_maps,hooks,mounts]
    gates=[leg_gate,brace_gate,tray_gate,hook_gate,mount_gate]
    signals={}
    for c in images:
        value=sets[0][c]
        for selector,group in zip(categories[1:],sets[1:]):value=mix(t,value,group[c],selector)
        signals[c]=value
    gate=0
    for selector,value in zip(categories,gates):gate=calc(t,'MAXIMUM',gate,calc(t,'MULTIPLY',selector,value))
    # The original generated albedo provides a second exact-location check of chip phase.
    from_color=calc(t,'SUBTRACT',1,smooth(t,luma(t,signals['BaseColor']),.10,.34))
    from_metal=smooth(t,signals['Metallic'],.04,.58)
    phase=calc(t,'MULTIPLY',gate,calc(t,'MINIMUM',from_color,from_metal))
    phase=mix(t,phase,calc(t,'MULTIPLY',leg_phase,leg_gate),categories[0])
    phase=mix(t,phase,calc(t,'MULTIPLY',brace_phase,brace_gate),categories[1])
    # Finite light polish on the lower hook arc follows real normals even where source J differs from mesh.
    hook_rub=calc(t,'MULTIPLY',categories[3],calc(t,'MULTIPLY',hook_gate,within(t,z,.583,.009)))
    irregular=smooth(t,noise(t,geo.outputs['Position'],650,2),.39,.63)
    hook_rub=calc(t,'MULTIPLY',hook_rub,irregular)
    phase=calc(t,'MAXIMUM',phase,calc(t,'MULTIPLY',hook_rub,.16))
    grain=noise(t,geo.outputs['Position'],1850,2)
    age=noise(t,geo.outputs['Position'],8,2)
    enamel=mix(t,(.42,.445,.45,1),(.38,.407,.415,1),calc(t,'MULTIPLY',age,.33))
    tray_dust=calc(t,'MULTIPLY',categories[2],calc(t,'MULTIPLY',
              calc(t,'MAXIMUM',smooth(t,calc(t,'ABSOLUTE',x),.195,.232),smooth(t,y,.095,.140)),
              calc(t,'SUBTRACT',1,smooth(t,z,.56,.59))))
    tray_dust=calc(t,'MULTIPLY',tray_dust,calc(t,'MULTIPLY',noise(t,geo.outputs['Position'],72),.22))
    enamel=mix(t,enamel,(.20,.185,.157,1),tray_dust)
    steel=mix(t,signals['BaseColor'],(.14,.15,.155,1),calc(t,'MULTIPLY',hook_rub,.65))
    link(t,mix(t,enamel,steel,phase),shader.inputs['Base Color'])
    rough=mix(t,.53,signals['Roughness'],phase)
    polished=calc(t,'ADD',categories[1],categories[3])
    rough=mix(t,rough,.31,calc(t,'MULTIPLY',phase,calc(t,'MULTIPLY',polished,.7)))
    link(t,rough,shader.inputs['Roughness'])
    metallic=calc(t,'MULTIPLY',phase,mix(t,signals['Metallic'],.84,calc(t,'MULTIPLY',hook_rub,.8)))
    link(t,metallic,shader.inputs['Metallic'])
    link(t,calc(t,'MULTIPLY',calc(t,'SUBTRACT',1,phase),.025),shader.inputs['Coat Weight'])
    shader.inputs['Coat Roughness'].default_value=.4
    height=calc(t,'ADD',.5,calc(t,'ADD',calc(t,'MULTIPLY',calc(t,'SUBTRACT',grain,.5),.018),
                    calc(t,'MULTIPLY',phase,calc(t,'ADD',-.14,calc(t,'MULTIPLY',calc(t,'SUBTRACT',signals['Height'],.5),.30)))))
    b=node(t,'ShaderNodeBump');link(t,height,b.inputs['Height']);b.inputs['Distance'].default_value=.00025
    link(t,b.outputs[0],shader.inputs['Normal'])
    return shader,{'Height':height,'Phase':phase}


def combined(objects,material,uv_name):
    """Make a disposable evaluated world-space bake mesh preserving UVs and split normals."""
    deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];uvs=[];normals=[];categories=[]
    for o in objects:
        m=bpy.data.meshes.new_from_object(o.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
        offset=len(verts);matrix=o.matrix_world;normal_matrix=matrix.to_3x3().inverted().transposed()
        verts.extend(tuple(matrix@v.co) for v in m.vertices)
        for p in m.polygons:
            faces.append(tuple(offset+i for i in p.vertices))
            for l in p.loop_indices:
                uvs.append(tuple(m.uv_layers[uv_name].data[l].uv))
                normals.append(tuple((normal_matrix@m.corner_normals[l].vector).normalized()))
                categories.append(o.color[0])
        bpy.data.meshes.remove(m)
    mesh=bpy.data.meshes.new('Regional bake temporary');mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name=uv_name)
    for q,v in zip(uv.data,uvs):q.uv=v
    for p in mesh.polygons:p.use_smooth=True
    mesh.normals_split_custom_set(normals)
    attr=mesh.attributes.new('MetalCategory','FLOAT','CORNER')
    for d,value in zip(attr.data,categories):d.value=value
    mesh.materials.append(material)
    ob=bpy.data.objects.new('Regional bake temporary',mesh);bpy.context.scene.collection.objects.link(ob)
    return ob


def author_preview():
    """Render finite shader fields on the actual evaluated asset before expensive final bakes."""
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    mat=bpy.data.materials[METAL];author=mat.copy();metal_author(author)
    objects=[o for o in bpy.data.objects if o.get('model_role')=='LOW' and o.active_material==mat]
    for o in objects:o.hide_render=True
    combined(objects,author,'UV_MetalPBR')
    setup()
    views=VIEWS[:5] if '--close' not in sys.argv else VIEWS[1:3]
    for view in views:render_view(view,'author',1600)


def rubber_author(material,old_images):
    """Retain generated rubber skin, but add unequal directional scuffs and localized floor dust."""
    t=material.node_tree;t.nodes.clear()
    shader=node(t,'ShaderNodeBsdfPrincipled');out=node(t,'ShaderNodeOutputMaterial')
    link(t,shader.outputs[0],out.inputs['Surface'])
    uv=node(t,'ShaderNodeUVMap');uv.uv_map='UV_CapsPBR'
    maps=texture_signals(t,uv.outputs[0],{c:old_images[c] for c in ['BaseColor','Roughness','Height']})
    norm=node(t,'ShaderNodeNormalMap');norm.uv_map='UV_CapsPBR';norm.space='TANGENT'
    tex=node(t,'ShaderNodeTexImage');tex.image=old_images['Normal_OpenGL'];tex.extension='EXTEND'
    link(t,uv.outputs[0],tex.inputs['Vector']);link(t,tex.outputs['Color'],norm.inputs['Color'])
    geo=node(t,'ShaderNodeNewGeometry');p=node(t,'ShaderNodeSeparateXYZ');n=node(t,'ShaderNodeSeparateXYZ')
    link(t,geo.outputs['Position'],p.inputs[0]);link(t,geo.outputs['Normal'],n.inputs[0])
    x,y,z=p.outputs;nx,ny,nz=n.outputs
    cap_id=calc(t,'ADD',calc(t,'GREATER_THAN',x,0),calc(t,'MULTIPLY',calc(t,'GREATER_THAN',y,0),2))
    s=calc(t,'MULTIPLY',calc(t,'ARCTAN2',ny,nx),.016)
    center=calc(t,'ADD',-.024,calc(t,'MULTIPLY',cap_id,.012))
    tilted=calc(t,'ADD',s,calc(t,'MULTIPLY',calc(t,'SUBTRACT',z,.015),.55))
    skin=calc(t,'SUBTRACT',1,smooth(t,calc(t,'ABSOLUTE',nz),.25,.75))
    scuff=calc(t,'MULTIPLY',within(t,tilted,center,.012,.5),within(t,z,.016,.011,.3))
    scuff=calc(t,'MULTIPLY',scuff,skin)
    thin=0
    for offset,zcenter,length in [(-.006,.015,.010),(.002,.012,.009),(.007,.019,.007)]:
        line_gate=calc(t,'MULTIPLY',within(t,tilted,calc(t,'ADD',center,offset),.00016,.6),within(t,z,zcenter,length,.15))
        thin=calc(t,'MAXIMUM',thin,line_gate)
    thin=calc(t,'MULTIPLY',thin,skin)
    # Discontinuous 2–5 mm ground-contact dust follows separate sectors, never a bright ring.
    dust=calc(t,'MULTIPLY',calc(t,'SUBTRACT',1,smooth(t,z,.001,.005)),within(t,s,calc(t,'SUBTRACT',.025,center),.016,.5))
    dust=calc(t,'MULTIPLY',dust,calc(t,'MULTIPLY',noise(t,geo.outputs['Position'],230),skin))
    base=mix(t,(.022,.025,.027,1),maps['BaseColor'],.32)
    base=mix(t,base,(.040,.044,.045,1),calc(t,'ADD',calc(t,'MULTIPLY',scuff,.38),calc(t,'MULTIPLY',thin,.58)))
    base=mix(t,base,(.050,.045,.037,1),calc(t,'MULTIPLY',dust,.32))
    link(t,base,shader.inputs['Base Color'])
    rough=mix(t,.62,maps['Roughness'],.22)
    rough=mix(t,rough,.46,calc(t,'MULTIPLY',scuff,.65))
    link(t,mix(t,rough,.73,dust),shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value=0;shader.inputs['IOR'].default_value=1.48
    shader.inputs['Coat Weight'].default_value=0
    height=calc(t,'ADD',.5,calc(t,'SUBTRACT',calc(t,'MULTIPLY',calc(t,'SUBTRACT',maps['Height'],.5),.35),calc(t,'MULTIPLY',thin,.05)))
    b=node(t,'ShaderNodeBump');link(t,height,b.inputs['Height']);b.inputs['Distance'].default_value=.00018
    link(t,norm.outputs[0],b.inputs['Normal']);link(t,b.outputs[0],shader.inputs['Normal'])
    return shader,{'Height':height,'Phase':scuff}


def baked_channel(obj,material,channel,resolution,folder,socket=None,signal=None):
    """Bake one actual evaluated surface channel; output linear data or encoded albedo PNG."""
    sc=bpy.context.scene;sc.cycles.samples=1
    sc.render.bake.use_selected_to_active=False;sc.render.bake.use_clear=True;sc.render.bake.margin=16
    sc.render.bake.normal_space='TANGENT'
    sc.render.bake.normal_r='POS_X';sc.render.bake.normal_g='POS_Y';sc.render.bake.normal_b='POS_Z'
    for o in sc.objects:o.select_set(o==obj)
    bpy.context.view_layer.objects.active=obj;obj.hide_set(False);obj.hide_render=False
    im=bpy.data.images.new('Regional bake target',width=resolution,height=resolution,alpha=False,float_buffer=True)
    im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color'
    t=material.node_tree
    for n in t.nodes:n.select=False
    target=node(t,'ShaderNodeTexImage');target.image=im;target.select=True;t.nodes.active=target
    out=next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL')
    previous=out.inputs['Surface'].links[0].from_socket;emission=None
    if channel!='Normal_OpenGL':
        emission=node(t,'ShaderNodeEmission')
        if socket:
            shader=next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED');value=shader.inputs[socket]
            signal=value.links[0].from_socket if value.is_linked else value.default_value
        if isinstance(signal,(int,float)):signal=(signal,signal,signal,1)
        link(t,signal,emission.inputs['Color']);link(t,emission.outputs[0],out.inputs['Surface'])
    print('REGIONAL_BAKE',folder.name,channel,flush=True)
    bpy.ops.object.bake(type='NORMAL' if channel=='Normal_OpenGL' else 'EMIT')
    if emission:link(t,previous,out.inputs['Surface']);t.nodes.remove(emission)
    folder.mkdir(parents=True,exist_ok=True);path=folder/f'KOKUYO_{channel}.png'
    settings=sc.render.image_settings
    saved=(settings.file_format,settings.color_mode,settings.color_depth,sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma)
    settings.file_format='PNG';settings.color_mode='RGB';settings.color_depth='16' if channel in ['Height','Normal_OpenGL'] else '8'
    sc.view_settings.view_transform='Standard' if channel=='BaseColor' else 'Raw'
    sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    im.save_render(str(path),scene=sc)
    settings.file_format,settings.color_mode,settings.color_depth=saved[:3]
    sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma=saved[3:]
    t.nodes.remove(target);bpy.data.images.remove(im)
    return {'path':str(path),'sha256':digest(path),'resolution':resolution,'depth':16 if channel in ['Height','Normal_OpenGL'] else 8}


def images_by_role(material):
    """Return the native final-channel image bindings without assuming image display names."""
    return {n.get('kokuyo_role'):n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.get('kokuyo_role') and n.image}


def bind_maps(material,rows):
    """Swap only final packed images; retain the current native shader graph and UV/normal connections."""
    for n in material.node_tree.nodes:
        channel=n.get('kokuyo_role')
        if n.type!='TEX_IMAGE' or channel not in rows:continue
        old=n.image;im=bpy.data.images.load(rows[channel]['path'],check_existing=False)
        im.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';im.pack();n.image=im
        if old and old.users==0:bpy.data.images.remove(old)


def build():
    """Bake component-specific metal/rubber fields and return to the protected source before binding."""
    baseline=json.loads((WORK/'baseline.json').read_text(encoding='utf-8'))
    assert digest(SOURCE)==baseline['sha256'],'Source changed; reconcile before final authoring'
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    mat=bpy.data.materials[METAL];author=mat.copy();shader,signals=metal_author(author)
    objects=[o for o in bpy.data.objects if o.get('model_role')=='LOW' and o.active_material==mat]
    for o in objects:o.hide_render=True
    temporary=combined(objects,author,'UV_MetalPBR');setup()
    metal={};folder=WORK/'metal_8k'
    for channel,socket in [('BaseColor','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('CoatWeight','Coat Weight')]:
        metal[channel]=baked_channel(temporary,author,channel,8192,folder,socket=socket)
    metal['Height']=baked_channel(temporary,author,'Height',8192,folder,signal=signals['Height'])
    metal['Normal_OpenGL']=baked_channel(temporary,author,'Normal_OpenGL',8192,folder)
    if '--reuse-rubber' in sys.argv:
        rubber=json.loads((WORK/'build.json').read_text(encoding='utf-8'))['rubber']
        assert all(digest(r['path'])==r['sha256'] for r in rubber.values())
    else:
        bpy.ops.wm.open_mainfile(filepath=str(INPUT))
        mat=bpy.data.materials[CAPS];old=images_by_role(mat);author=mat.copy();shader,signals=rubber_author(author,old)
        objects=[o for o in bpy.data.objects if o.get('model_role')=='LOW' and o.active_material==mat]
        for o in objects:o.hide_render=True
        temporary=combined(objects,author,'UV_CapsPBR');setup()
        rubber={};folder=WORK/'rubber_4k'
        for channel,socket in [('BaseColor','Base Color'),('Roughness','Roughness')]:
            rubber[channel]=baked_channel(temporary,author,channel,4096,folder,socket=socket)
        rubber['Height']=baked_channel(temporary,author,'Height',4096,folder,signal=signals['Height'])
        rubber['Normal_OpenGL']=baked_channel(temporary,author,'Normal_OpenGL',4096,folder)
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    bind_maps(bpy.data.materials[METAL],metal);bind_maps(bpy.data.materials[CAPS],rubber)
    bpy.data.materials[METAL]['regional_wear']='Finite imagegen fields: upper footrest crown; uneven vertical impacts; book slides/mouth; loaded hook arcs; sparse plate corners'
    bpy.data.materials[CAPS]['regional_wear']='Four unequal oblique rubs; finite shallow lines; discontinuous ground dust; dark rubber skin'
    assert fingerprint()==baseline['protected'],'Protected mesh, UV, normal or transforms changed'
    assert protected_other()==baseline['protected_other'],'Protected wood/AO/scene changed'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    (WORK/'build.json').write_text(json.dumps({'metal':metal,'rubber':rubber,'candidate_sha256':digest(TARGET),'source_sha256':baseline['sha256'],'protected':True},indent=2),encoding='utf-8')
    print('REGIONAL_BUILD_OK',flush=True)


def render():
    """Independently open the final atlas candidate and inspect six matching actual mesh views."""
    bpy.ops.wm.open_mainfile(filepath=str(TARGET));setup()
    bpy.context.scene.cycles.samples=96
    views=VIEWS if '--hardware' not in sys.argv else VIEWS[3:5]
    for view in views:render_view(view,'after',1800)


def motion():
    """Render a real continuous camera orbit to 24 temporary frames for material stability inspection."""
    bpy.ops.wm.open_mainfile(filepath=str(TARGET));setup()
    bpy.context.scene.cycles.samples=32
    for i in range(24):
        t=i/23
        view=(f'orbit_{i:03d}',-65+40*t,14+3*t,(0,0,.335),2.30,70)
        render_view(view,'motion',800)


def surface_points(material,uv_name):
    """Sample actual native UV triangles at four barycentric positions, retaining physical regions."""
    rows=[]
    for o in bpy.data.objects:
        if o.get('model_role')!='LOW' or o.active_material!=material:continue
        m=o.data;m.calc_loop_triangles();uv=m.uv_layers[uv_name]
        for tri in m.loop_triangles:
            for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
                co=Vector((0,0,0));tex=Vector((0,0));normal=Vector((0,0,0))
                for l,w in zip(tri.loops,weights):
                    co+=(o.matrix_world@m.vertices[m.loops[l].vertex_index].co)*w
                    tex+=uv.data[l].uv*w
                    normal+=(o.matrix_world.to_3x3()@m.corner_normals[l].vector)*w
                rows.append([o.name,tuple(tex),tuple(co),tuple(normal.normalized()),o.color[0]])
    return rows


def sample_image(image,points):
    """Read only sampled values from actual bound Blender image pixels, releasing the full buffer."""
    buf=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(buf)
    w,h=image.size
    indices=[]
    for point in points:
        u,v=point[1];x,y=int(u*w),int(v*h)
        assert 0<=x<w and 0<=y<h,'Surface UV outside final atlas'
        indices.append(y*w+x)
    result=buf.reshape(-1,4)[np.asarray(indices),:3].copy();del buf
    return result


def verify():
    """Independently reopen candidate; verify protected content, real region coverage and nonblank normals."""
    baseline=json.loads((WORK/'baseline.json').read_text(encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=str(TARGET))
    assert fingerprint()==baseline['protected'];assert protected_other()==baseline['protected_other']
    mat=bpy.data.materials[METAL];points=surface_points(mat,'UV_MetalPBR');images=images_by_role(mat)
    metallic=sample_image(images['Metallic'],points)[:,0]
    normals=sample_image(images['Normal_OpenGL'],points)
    assert np.isfinite(normals).all()
    unit=np.linalg.norm(normals*2-1,axis=1)
    assert np.min(unit)>.82 and np.max(unit)<1.15,(float(unit.min()),float(unit.max()))
    assert (normals[:,2]>.35).all(),'Black, inverted or blank normal surface'
    categories=np.asarray([p[4] for p in points]);world_normals=np.asarray([p[3] for p in points])
    regions={}
    for cat,name in [(0,'frame'),(.25,'footrest'),(.5,'cubby'),(.75,'hooks'),(1,'mounts')]:
        selected=np.abs(categories-cat)<.04
        regions[name]={'samples':int(selected.sum()),'exposed_percent':float((metallic[selected]>.055).mean()*100),
                       'mean_metallic':float(metallic[selected].mean()),'normal_std':np.std(normals[selected],axis=0).tolist()}
    brace=np.abs(categories-.25)<.04;top=brace&(world_normals[:,2]>.3);under=brace&(world_normals[:,2]<-.3)
    regions['footrest']['crown_mean_metallic']=float(metallic[top].mean())
    regions['footrest']['underside_mean_metallic']=float(metallic[under].mean())
    assert metallic[top].mean()>metallic[under].mean()+.10,'Crown and underside wear not distinguished'
    assert regions['frame']['exposed_percent']>8,'Legs became unrealistically new'
    assert regions['cubby']['exposed_percent']<regions['frame']['exposed_percent'],'Cubby should not inherit tube-like mottling'
    cap_points=surface_points(bpy.data.materials[CAPS],'UV_CapsPBR')
    cap_images=images_by_role(bpy.data.materials[CAPS]);cap_normal=sample_image(cap_images['Normal_OpenGL'],cap_points)
    assert np.isfinite(cap_normal).all() and (cap_normal[:,2]>.35).all()
    assert np.max(np.std(cap_normal,axis=0))>.003,'Rubber normal empty'
    per_cap={}
    for name in sorted({p[0] for p in cap_points}):
        selected=np.asarray([p[0]==name for p in cap_points])
        per_cap[name]={'normal_std':np.std(cap_normal[selected],axis=0).tolist(),'samples':int(selected.sum())}
    for im in images.values():assert im.packed_file
    for im in cap_images.values():assert im.packed_file
    result={'technical_status':'pass','visual_status':'review','candidate_sha256':digest(TARGET),
            'source_sha256':baseline['sha256'],'geometry_all_UVs_normals_wood_AO_scene_preserved':True,
            'regions':regions,'metal_sample_count':len(points),'metal_normal_unit_range':[float(unit.min()),float(unit.max())],
            'rubber_samples':len(cap_points),'caps':per_cap,'normal_convention':'OpenGL',
            'coordinates':'Each full-height leg strip used once; four unequal footrest corridors; finite sheet/hook/plate contacts; 4 rubber sectors',
            'generated_native_resolution':[1254,1254],'final_atlas_sizes':{'metal':8192,'rubber':4096},
            'reference':'Private user desk collage, lower two real metal photos; exact use history is reconstruction',
            'input_sources':{p.name:digest(p) for p in WORK.glob('*.png') if p.name in ['BaseColor.png','Metallic.png','Roughness.png','Height.png','Leg_BaseColor.png','Leg_Phase.png','Brace_BaseColor.png']}}
    (WORK/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGIONAL_VERIFY_OK',json.dumps(regions),flush=True)


def deliver():
    """Reconcile native source/dependencies, then update final maps and relative packed paths in place."""
    baseline=json.loads((WORK/'baseline.json').read_text(encoding='utf-8'))
    check=json.loads((WORK/'verification.json').read_text(encoding='utf-8'))
    built=json.loads((WORK/'build.json').read_text(encoding='utf-8'))
    assert check['technical_status']=='pass' and check['candidate_sha256']==digest(TARGET)
    assert digest(SOURCE)==baseline['sha256'],'User saved new native state; reconcile before delivering'
    for path,sha in baseline['dependencies'].items():assert digest(ROOT/path)==sha,'User changed a dependency; reconcile first'
    rows={}
    for group,folder in [('metal','metal_8k'),('rubber','rubber_4k')]:
        rows[group]={}
        for channel,row in built[group].items():
            assert digest(row['path'])==row['sha256']
            dst=ROOT/'02_assets/textures/generated/kokuyo_desk'/folder/Path(row['path']).name
            shutil.copy2(row['path'],dst);rows[group][channel]={**row,'path':str(dst)}
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bind_maps(bpy.data.materials[METAL],rows['metal']);bind_maps(bpy.data.materials[CAPS],rows['rubber'])
    bpy.data.materials[METAL]['regional_wear']='Finite upper-crown polish; varied vertical chip clusters; book slides and rolled mouth; unequal hook-wire contact; limited mounting corners'
    bpy.data.materials[CAPS]['regional_wear']='Four distinct oblique shallow scuffs and discontinuous floor dust over molded rubber'
    for im in bpy.data.images:
        if im.source!='FILE':continue
        # Old unchanged wood/AO sources are resolved from their original relative paths.
        path=Path(bpy.path.abspath(im.filepath))
        assert path.is_file(),str(path)
        relative='//'+os.path.relpath(path,SOURCE.parent).replace('\\','/')
        if im.packed_file:im.unpack(method='REMOVE')
        im.filepath=relative;im.reload();im.pack()
    assert fingerprint()==baseline['protected'];assert protected_other()==baseline['protected_other']
    assert digest(SOURCE)==baseline['sha256'],'Source saved during binding; delivery stopped'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),compress=True)
    (WORK/'delivery.json').write_text(json.dumps({'source_sha256':baseline['sha256'],'delivered_sha256':digest(SOURCE),'updated_maps':rows},indent=2),encoding='utf-8')
    print('REGIONAL_DELIVERY_OK',digest(SOURCE),flush=True)


def reopen_delivery():
    """Verify the delivered native file independently and compare all external/packed dependency bytes."""
    baseline=json.loads((WORK/'baseline.json').read_text(encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    assert fingerprint()==baseline['protected'];assert protected_other()==baseline['protected_other']
    deps=[]
    for im in bpy.data.images:
        if im.source!='FILE':continue
        assert im.filepath.startswith('//') and im.packed_file
        path=Path(bpy.path.abspath(im.filepath));assert path.is_file()
        sha=digest(path);assert hashlib.sha256(im.packed_file.data).hexdigest()==sha
        assert 'cache' not in im.filepath and 'worktrees' not in im.filepath
        assert all('worktrees' not in f.filepath and 'cache' not in f.filepath for f in im.packed_files)
        deps.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha,'size':list(im.size)})
    assert len(deps)==21,len(deps)
    result=json.loads((WORK/'verification.json').read_text(encoding='utf-8'))
    result.update(delivered_sha256=digest(SOURCE),dependencies=deps,independent_delivery_reopen=True,relative_paths_and_packed_bytes_identical=True)
    out=Path(__file__).with_name('verification.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('REGIONAL_DELIVERED_REOPEN_OK',result['delivered_sha256'],len(deps),flush=True)


if __name__=='__main__':
    action=sys.argv[sys.argv.index('--')+1]
    globals()[action]()
