"""Rebuild five classroom equipment assets; preserve published collection offsets and front -Y.

Inputs: catalog pivots, original film reference, authored 2K maps. Output: isolated work blend.
Geometry uses metres, direct meshes, thin-sheet profiles and separate hardware, never subdivision as detail.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
TEX=ROOT/'02_assets/textures/authored/equipment_rebuild'
CACHE=ROOT/'07_pipeline/cache/equipment_rebuild';CACHE.mkdir(parents=True,exist_ok=True)
REVIEW=ROOT/'06_review/equipment_rebuild';REVIEW.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
catalog=json.loads((ROOT/'07_pipeline/cache/equipment_rebuild/original.json').read_text())
cols={};active=None;pivot=Vector((0,0,0))

def material(name,family,metal=0,bump=.000035):
    """Build a family material from 2K maps; UVs use metres and tile every 0.25 m."""
    m=bpy.data.materials.new('EQ '+name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Metallic'].default_value=metal
    uv=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=4;l.new(uv.outputs['UV'],scale.inputs[0])
    for channel,socket in [('color','Base Color'),('roughness','Roughness'),('height','Normal')]:
        t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(TEX/f'{family}_{channel}_2k.png'),check_existing=True);t.image.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color';l.new(scale.outputs[0],t.inputs['Vector'])
        if channel=='height':
            b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=bump;b.inputs['Strength'].default_value=.3;l.new(t.outputs['Color'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs[socket])
        else:l.new(t.outputs['Color'],p.inputs[socket])
    m['tile_metres']=.25;m['source']='Original authored maps, equipment_textures.py, seed 91126';m['bump_distance_metres']=bump
    return m
enamel=material('aged warm enamel','enamel');plastic=material('grey olive ABS','abs');metal=material('zinc steel','metal',.8);rubber=material('rubber gasket','rubber');dark=material('dark graphite','dark');paper=material('warm dial paper','paper');glass=material('CRT face glass','glass',.12,.000006)
glass.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.45
clear=material('clock clear cover','glass',0,.000002)
cp=clear.node_tree.nodes.get('Principled BSDF');cp.inputs['Transmission Weight'].default_value=1;cp.inputs['Roughness'].default_value=.06
# Clear glass uses pale neutral tint, retaining 2K roughness/height maps without absorbing the dial.
for link in list(cp.inputs['Base Color'].links):clear.node_tree.links.remove(link)
cp.inputs['Base Color'].default_value=(.94,.96,.94,1)
tube=material('unlit phosphor glass','paper',0,.000012)
tp=tube.node_tree.nodes.get('Principled BSDF');tp.inputs['Coat Weight'].default_value=.25

def collection(name):
    """Activate a preserved asset collection, return it, and set the local-to-world origin."""
    global active,pivot
    active=bpy.data.collections.new(name);scene.collection.children.link(active);active.instance_offset=catalog[name]['pivot'];pivot=Vector(active.instance_offset)
    active.asset_mark();active.asset_data.description='Rebuilt from dro:p 02:32–02:52; original proportions, separate industrial parts, metric 2K surfaces'
    active['asset_id']=name;active['front_axis']='-Y';active['version']='equipment_rebuild_2026-09-11';cols[name]=active
    return active

def mesh(name,verts,faces,mat,bevel=0,smooth=False):
    """Make a local metre mesh with metric planar UVs, material and optional real edge bevel."""
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);active.objects.link(ob);ob.location=pivot
    if mat:me.materials.append(mat)
    uv=me.uv_layers.new(name='UVMap')
    for f in me.polygons:
        f.use_smooth=smooth;axis=max(range(3),key=lambda a:abs(f.normal[a]));axes=[a for a in range(3) if a!=axis]
        for li in f.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])
    if bevel:
        b=ob.modifiers.new('Bevel','BEVEL');b.width=bevel;b.segments=3
        b=ob.modifiers.new('Weighted Normal','WEIGHTED_NORMAL')
    return ob

def box(name,c,s,mat=enamel,bevel=.001):
    """Return a bevelled panel at centre c with size s in metres."""
    vs=[(c[0]+x*s[0]/2,c[1]+y*s[1]/2,c[2]+z*s[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    return mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat,bevel)

def rod(name,a,b,r,mat=metal,n=48):
    """Return a cylinder between endpoints a/b with radius r; radial UV circumference is metric."""
    a=Vector(a);b=Vector(b);v=b-a;q=v.to_track_quat('Z','Y');vs=[]
    for z in [0,v.length]:
        for i in range(n):vs.append(tuple(a+q@Vector((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z))))
    fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=mesh(name,vs,fs,mat,0,True)
    for f in ob.data.polygons[:2]:f.use_smooth=False
    return ob

def path(name,points,r,mat=metal):
    """Create round wire/rolled edge from centreline points, radius r and material."""
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,cu);active.objects.link(ob);ob.location=pivot;cu.materials.append(mat);return ob

def circle(name,c,r,wire,mat=metal):
    """Create a closed ring in local X/Z plane, facing classroom -Y."""
    return path(name,[(c[0]+r*math.sin(i*math.tau/96),c[1],c[2]+r*math.cos(i*math.tau/96)) for i in range(97)],wire,mat)

def screw(c,r=.003,axis='Y'):
    """Make a screw head, washer and recessed cross, facing -Y or downward -Z."""
    v=Vector((0,-1,0) if axis=='Y' else (0,0,-1));c=Vector(c)
    rod('EQ fastener washer',c,c+v*.001,r*1.4);rod('EQ fastener head',c+v*.001,c+v*.003,r)
    size=(r*1.45,.0005,.0008) if axis=='Y' else (r*1.45,.0008,.0005)
    box('EQ screw recessed slot',c+v*.0031,size,dark,.0001)
    size=(.0008,.0005,r*1.45) if axis=='Y' else (.0008,r*1.45,.0005)
    box('EQ screw recessed slot',c+v*.0032,size,dark,.0001)

def rounded_loop(w,h,r,y,z=0):
    """Return 64 rounded rectangle points on X/Z plane; input dimensions/radius in metres."""
    pts=[]
    for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for i in range(16):
            a=math.radians(start+i*90/15);pts.append((cx+r*math.cos(a),y,z+cz+r*math.sin(a)))
    return pts

def profiles(name,sections,mat,closed=False):
    """Loft successive rounded rectangle section tuples (w,h,r,y,z); makes a bezel or tapered case."""
    vs=sum([rounded_loop(*s) for s in sections],[]);n=64;fs=[]
    for j in range(len(sections)-1):
        for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    if closed:fs.extend([tuple(range(n-1,-1,-1)),tuple(range((len(sections)-1)*n,len(sections)*n))])
    return mesh(name,vs,fs,mat,.0008,True)

# Twin fluorescent assembly: bent thin steel channel, rolled perimeter, sockets, pins, collars and latches.
collection('AST_fluorescent_fixture')
box('EQ lamp ballast case',(0,0,.005),(.12,1.29,.05),enamel,.003)
profile=[(-.13,-.036),(-.126,-.03),(-.085,-.018),(-.048,-.006),(.048,-.006),(.085,-.018),(.126,-.03),(.13,-.036)]
vs=[(x,y,z) for y in [-.635,.635] for x,z in profile];fs=[(i,i+1,i+1+len(profile),i+len(profile)) for i in range(len(profile)-1)]
ob=mesh('EQ lamp folded reflector 0.8mm',vs,fs,enamel,.0008);s=ob.modifiers.new('Solidify','SOLIDIFY');s.thickness=.0008
for x in [-.129,.129]:rod('EQ lamp rolled safety edge',(x,-.635,-.035),(x,.635,-.035),.0017,enamel)
for y in [-.636,.636]:
    box('EQ lamp folded end plate',(0,y,-.005),(.25,.0012,.051),enamel,.001)
    box('EQ lamp ceiling clip',(0,y*.76,.043),(.12,.035,.014),metal,.002)
    screw((0,y*.72,-.022),.004,'Z')
for x in [-.066,.066]:
    rod('EQ lamp fluorescent phosphor tube',(x,-.548,-.087),(x,.548,-.087),.0188,tube,64)
    for y in [-.566,.566]:
        rod('EQ lamp aluminium end cap',(x,y-.016,-.087),(x,y+.016,-.087),.0193,metal,64)
        box('EQ lamp ceramic lampholder',(x,y*1.065,-.059),(.047,.033,.073),enamel,.009)
        for xx in [-.006,.006]:rod('EQ lamp G13 contact pin',(x+xx,y,-.086),(x+xx,y*1.054,-.086),.0014,metal,24)
        screw((x,y*1.064,-.098),.0027,'Z')
for y in [-.30,.30]:
    rod('EQ lamp starter housing',(0,y,-.024),(0,y,-.049),.009,enamel)
    circle('EQ lamp starter contact seam',(0,y,-.045),.008,.0005,metal)

# CRT dimensions retain legacy shell and feet position; curved face and housing have different profiles.
collection('AST_crt_television')
crt_front=profiles('EQ CRT front moulded shell',[(.83,.69,.026,-.305,.355),(.83,.69,.026,-.20,.355),(.815,.675,.035,.09,.355)],plastic)
solid=crt_front.modifiers.new('Solidify','SOLIDIFY');solid.thickness=.003
crt_rear=profiles('EQ CRT rear tapered housing',[(.810,.67,.033,.096,.355),(.724,.59,.045,.22,.355),(.63,.52,.05,.373,.355)],plastic,False)
profiles('EQ CRT case mould split',[(.817,.675,.03,.088,.355),(.817,.675,.03,.094,.355)],dark)
# Annular front fascia surrounds the actual recessed 4:3 screen, avoiding a solid box over the glass.
profiles('EQ CRT face surround',[(.83,.69,.026,-.306,.355),(.77,.624,.022,-.329,.355),(.701,.516,.034,-.330,.407),(.671,.492,.04,-.319,.407)],plastic)
profiles('EQ CRT black screen bezel',[(.704,.521,.033,-.331,.407),(.673,.493,.04,-.34,.407),(.650,.472,.043,-.325,.407)],dark)
nu,nv=64,48;vs=[];fs=[]
for j in range(nv+1):
    v=j/nv*2-1
    for i in range(nu+1):
        u=i/nu*2-1;x=u*.327*(1-.045*abs(v)**12);z=.407+v*.238*(1-.06*abs(u)**12)
        vs.append((x,-.366+.037*(u*u*.75+v*v*.25),z))
for j in range(nv):
    for i in range(nu):a=j*(nu+1)+i;fs.append((a,a+nu+1,a+nu+2,a+1))
ob=mesh('EQ CRT thick convex screen',vs,fs,glass,0,True);s=ob.modifiers.new('Solidify','SOLIDIFY');s.thickness=.012
box('EQ CRT control strip',(0,-.334,.080),(.718,.024,.061),dark,.004)
for i in range(31):
    box('EQ CRT lower speaker grille rib',(-.32+i*.010,-.351,.079),(.003,.007,.034),plastic,.001)
for x in [.13,.22,.30]:
    box('EQ CRT inset control surround',(x,-.35,.08),(.045,.008,.034),plastic,.004)
    box('EQ CRT physical button',(x,-.358,.08),(.030,.011,.016),dark,.002)
box('EQ CRT indicator lens',(.078,-.36,.079),(.006,.003,.004),enamel,.001)
# Side vent openings are cut with Boolean meshes, so ribs reveal actual cavity rather than painted lines.
vent_cutters=[]
for side in [-1,1]:
    for y in [-.08,-.035,.01,.055]:
        cutter=box('EQ temporary vent cutter',(side*.412,y,.44),(.05,.019,.21),None,0);vent_cutters.append(cutter)
        box('EQ CRT recessed side vent',(side*.395,y,.44),(.003,.019,.21),dark,.002)
        for z in [.35,.397,.444,.491,.538]:box('EQ CRT vent angled louvre',(side*.414,y,z),(.008,.020,.007),plastic,.001)
# Apply the shell thickness and eight cutters together; delete only temporary authored cutter objects.
bpy.context.view_layer.objects.active=crt_front
for mod in list(crt_front.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
bm=bmesh.new();bm.from_mesh(crt_front.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(crt_front.data);bm.free()
for cutter in vent_cutters:
    mod=crt_front.modifiers.new('Boolean','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
# Build the rear grille as an explicit open panel: no overlapping cap can cover its apertures.
profiles('EQ CRT rear grille perimeter',[(.63,.52,.05,.373,.355),(.552,.218,.003,.373,.43)],plastic)
box('EQ CRT rear grille dark interior',(0,.360,.43),(.552,.002,.218),dark,.001)
for i in range(21):
    x=-.264+i*.0264
    box('EQ CRT rear vent separation rib',(x,.373,.43),(.012,.004,.218),plastic,.0006)
for x in [-.335,.335]:
    for z in [.10,.625]:screw((x,-.307,z),.0035)
for x in [-.265,.265]:
    # Extend the existing foot downward to meet the cabinet's 1.1775 m top; no instance transform changes.
    box('EQ CRT rubber foot',(x,-.035,-.032),(.105,.34,.070),rubber,.006)
    box('EQ CRT foot rail',(x,-.035,.010),(.11,.36,.014),dark,.002)
box('EQ CRT rear sockets recess',(0,.378,.16),(.29,.007,.084),dark,.004)
for x in [-.07,0,.07]:
    circle('EQ CRT RCA socket metal collar',(x,.386,.16),.008,.0017,metal)
    rod('EQ CRT RCA socket hollow',(x,.385,.16),(x,.388,.16),.0045,dark)
# Keep the legacy loose power cable below the television; it fits behind the existing cabinet.
path('EQ CRT power cord',[(.25,.372,.16),(.27,.394,-.1),(.25,.42,-.50),(.20,.42,-.87),(-.06,.40,-1.05),(-.26,.37,-.95)],.004,rubber)
box('EQ CRT cable strain relief',(.25,.375,.16),(.017,.02,.029),rubber,.003)

# Painted equipment cabinet: real separate sheet doors, rolled returns, hinge leaves and usable pulls.
collection('AST_equipment_cabinet')
door_mat=enamel.copy();door_mat.name='EQ cabinet door enamel with contact wear'
n=door_mat.node_tree.nodes;l=door_mat.node_tree.links;p=n.get('Principled BSDF');coord=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');combine=n.new('ShaderNodeCombineXYZ');l.new(coord.outputs['Generated'],sep.inputs[0]);l.new(sep.outputs['X'],combine.inputs['X']);l.new(sep.outputs['Z'],combine.inputs['Y'])
for channel,socket in [('color','Base Color'),('roughness','Roughness')]:
    t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(TEX/f'cabinet_door_{channel}_2k.png'),check_existing=True);t.image.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color';l.new(combine.outputs[0],t.inputs['Vector']);l.new(t.outputs['Color'],p.inputs[socket])
door_mat['full_face_metres']=[.53,1.112];door_mat['wear_intent']='Dust at folds, lower grime, gentle hand polish near pull'
for x in [-.54,.54]:box('EQ cabinet side folded panel',(x,0,.59),(.025,.65,1.18),enamel,.003)
for z in [.035,.57,1.165]:box('EQ cabinet shelf with rolled nose',(0,0,z),(1.06,.64,.025),enamel,.003)
box('EQ cabinet rear removable panel',(0,.31,.59),(1.06,.022,1.13),enamel,.001)
box('EQ cabinet recessed toe plinth',(0,0,.032),(1.025,.59,.058),dark,.003)
for x in [-.273,.273]:
    box('EQ cabinet independent door skin',(x,-.346,.588),(.53,.004,1.112),door_mat,.001)
    for xx in [x-.26,x+.26]:box('EQ cabinet door folded vertical return',(xx,-.336,.588),(.009,.026,1.11),enamel,.001)
    for z in [.036,1.14]:box('EQ cabinet door folded horizontal return',(x,-.335,z),(.514,.026,.012),enamel,.001)
    hx=x+(.17 if x<0 else -.17)
    for z in [.53,.65]:
        box('EQ cabinet pull escutcheon',(hx,-.352,z),(.026,.003,.027),metal,.003)
        rod('EQ cabinet handle standoff',(hx,-.352,z),(hx,-.381,z),.005,metal)
    path('EQ cabinet curved pull',[(hx,-.375,.53),(hx,-.389,.542),(hx,-.389,.638),(hx,-.375,.65)],.006,metal)
    for z in [.22,.92]:
        xx=x+(-.248 if x<0 else .248)
        box('EQ cabinet hinge leaf',(xx,-.352,z),(.035,.004,.052),metal,.001)
        rod('EQ cabinet hinge barrel',(xx,-.358,z-.032),(xx,-.358,z+.032),.0053,metal)
        for zz in [-.016,.016]:screw((xx+(.009 if x<0 else -.009),-.356,z+zz),.0024)
        for zz in [-.013,.013]:circle('EQ cabinet hinge seam',(xx,-.358,z+zz),.0055,.0004,dark)
rod('EQ cabinet cam lock',(0.058,-.352,.60),(.058,-.357,.60),.011,metal)
box('EQ cabinet lock slot',(.058,-.359,.60),(.0015,.001,.012),dark,.0002)
for x in [-.505,.505]:
    for z in [.10,1.07]:screw((x,.325,z),.0028)

# Wall clock, with discrete stepped metal bezel, printed dial, shaped hands and cover thickness.
collection('AST_wall_clock')
rod('EQ clock rear casing',(0,-.008,0),(0,.075,0),.18,plastic,128)
rod('EQ clock dial backing',(0,-.071,0),(0,-.014,0),.171,enamel,128)
circle('EQ clock outer rolled bezel',(0,-.078,0),.171,.008,metal)
circle('EQ clock rubber cover gasket',(0,-.084,0),.163,.0023,rubber)
dial=paper.copy();dial.name='EQ clock dial print';n=dial.node_tree.nodes;l=dial.node_tree.links;p=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(TEX/'clock_dial_color_2k.png'))
l.new(t.outputs['Color'],p.inputs['Base Color'])
ob=rod('EQ clock printed face',(0,-.074,0),(0,-.075,0),.159,dial,128)
for f in ob.data.polygons:
    for li in f.loop_indices:
        co=ob.data.vertices[ob.data.loops[li].vertex_index].co;ob.data.uv_layers[0].data[li].uv=(.5+co.x/.318,.5+co.z/.318)
for angle,length,width in [(105,.09,.011),(180,.131,.007)]:
    a=math.radians(angle);axis=Vector((math.sin(a),0,math.cos(a)));side=Vector((math.cos(a),0,-math.sin(a)))
    verts=[tuple(axis*d+side*w+Vector((0,-.083,0))) for d,w in [(-.018,-width/2),(-.018,width/2),(length*.7,width*.32),(length,0),(length*.7,-width*.32)]]
    ob=mesh('EQ clock tapered metal hand',verts,[tuple(range(5))],dark,.0003);s=ob.modifiers.new('Solidify','SOLIDIFY');s.thickness=.0007
rod('EQ clock hand pivot',(0,-.084,0),(0,-.09,0),.006,metal)
rod('EQ clock 2mm glass cover',(0,-.091,0),(0,-.093,0),.161,clear,128)
box('EQ clock wall mounting shoe',(0,.072,.07),(.04,.008,.057),metal,.002)

# Public-address speaker: framed grille with actual hole geometry, recessed cone and wall shoe.
collection('AST_wall_speaker')
box('EQ speaker rear box',(0,.005,0),(.32,.23,.28),enamel,.008)
box('EQ speaker front baffle',(0,-.114,0),(.293,.018,.253),dark,.005)
profiles('EQ speaker removable grille border',[(.309,.269,.015,-.124,0),(.288,.247,.011,-.135,0),(.268,.228,.009,-.135,0)],enamel)
rod('EQ speaker hidden cone surround',(0,-.128,0),(0,-.13,0),.099,rubber,96)
rod('EQ speaker hidden cone',(0,-.131,0),(0,-.133,0),.077,dark,96)
# Fine strip grid is a truly open grille; the front baffle remains dark and separated in depth.
for i in range(67):
    x=-.132+i*.004
    box('EQ speaker perforation vertical web',(x,-.137,0),(.0011,.0013,.224),enamel,.0002)
for i in range(57):
    z=-.112+i*.004
    box('EQ speaker perforation horizontal web',(0,-.137,z),(.265,.0013,.0011),enamel,.0002)
for x in [-.14,.14]:
    for z in [-.113,.113]:screw((x,-.133,z),.0022)
    box('EQ speaker wall shoe',(x,.104,0),(.025,.026,.18),metal,.002)
box('EQ speaker bottom connection recess',(0,.12,-.083),(.084,.008,.046),dark,.002)
for x in [-.018,.018]:screw((x,.124,-.083),.0025)

# Isolated review rig stays separate from the five exported collection assets.
active=bpy.data.collections.new('EQ_review_rig');scene.collection.children.link(active);pivot=Vector((0,0,0))
floor=box('EQ review ground',(0,0,-1.5),(200,200,.05),enamel,.0)
world=bpy.data.worlds.new('EQ neutral studio');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.25,.25,.25,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.4;scene.world=world
for name,loc,power,size in [('EQ key',(-5,-4,7),950,5),('EQ fill',(4,-1,4),600,4),('EQ rim',(1,6,6),1000,3)]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ob=bpy.data.objects.new(name,ld);active.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((-1,3,1))-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('EQ review camera');cam=bpy.data.objects.new('EQ review camera',cd);active.objects.link(cam);scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.device='CPU';scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.image_settings.file_format='PNG'
cam.location=(-5,.2,2.6);target=Vector((-3.11,3.97,1.12));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=2.55
bpy.context.view_layer.update()
report={'assets':[],'front_axis':'-Y','metres':True,'texture_manifest':'02_assets/textures/authored/equipment_rebuild/texture_manifest.json'}
dg=bpy.context.evaluated_depsgraph_get()
for name,c in cols.items():
    pts=[o.matrix_world@Vector(v) for o in c.all_objects for v in o.bound_box];lo=[min(v[k] for v in pts) for k in range(3)];hi=[max(v[k] for v in pts) for k in range(3)]
    faces=sum(len(o.evaluated_get(dg).to_mesh().polygons) for o in c.all_objects if o.type=='MESH')
    report['assets'].append({'asset_id':name,'instance_offset':list(c.instance_offset),'objects':len(c.all_objects),'evaluated_faces':faces,'bounds_min':lo,'bounds_max':hi,'dimensions_metres':[hi[k]-lo[k] for k in range(3)]})
report['missing_images']=[im.filepath for im in bpy.data.images if im.source=='FILE' and not Path(bpy.path.abspath(im.filepath)).exists()]
report['all_images_at_least_2k']=all(min(im.size)>=2048 for im in bpy.data.images if im.source=='FILE')
(CACHE/'validation.json').write_text(json.dumps(report,indent=2))
out=ROOT/'02_assets/work/classroom_equipment.blend'
for im in bpy.data.images:
    if im.source=='FILE':im.filepath=bpy.path.relpath(im.filepath,start=str(out.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print(json.dumps(report,indent=2))
