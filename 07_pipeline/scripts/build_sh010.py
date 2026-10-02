"""Recreate the supplied classroom frame as editable Blender geometry.

Input: visual reference BV18V411f7Qf / user screenshot.
Output: separate scene, named collections, .blend and camera render.
Units: metres. Front wall is +Y; window wall is -X.
"""
import bpy
import math
import random
import json
import sys
from mathutils import Vector
from pathlib import Path

random.seed(41)
ROOT = Path(__file__).resolve().parents[2]
VERSION = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v001'
OUT = ROOT/'03_shots/sq010/sh010/work'
BLEND = OUT/f'drop_sq010_sh010_lookdev_{VERSION}.blend'
assert not BLEND.exists(), f'Refusing to overwrite {BLEND}'
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.data.scenes.new('sq010_sh010')
bpy.context.window.scene = scene

# Each category remains separately editable in the Outliner.
def collection(name):
    """Create a named collection under the new scene; return its datablock."""
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

arch = collection('env_classroom')
furn = collection('prp_desks')
props = collection('prp_classroom')
curt = collection('env_curtains')
candy = collection('chr_tin_figure')
lights = collection('lgt_sh010')
active_collection = arch

def material(name, color, rough=.5, metal=0):
    """Build a Principled material from RGB, roughness and metallic values."""
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m

def textured(name, dark, light, stretch=(1,1,1), scale=5, rough=.6, bump=.1):
    """Create noise-based colour and micro-bump; stretch controls grain direction."""
    m = material(name, light, rough)
    n, l = m.node_tree.nodes, m.node_tree.links
    tex = n.new('ShaderNodeTexCoord')
    vec = n.new('ShaderNodeVectorMath'); vec.operation = 'MULTIPLY'
    vec.inputs[1].default_value = stretch
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 3
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .15
    ramp.color_ramp.elements[0].color = (*dark,1)
    ramp.color_ramp.elements[1].position = .85
    ramp.color_ramp.elements[1].color = (*light,1)
    b = n.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump
    b.inputs['Distance'].default_value = .015
    p=n.get('Principled BSDF')
    l.new(tex.outputs['Generated'],vec.inputs[0]); l.new(vec.outputs[0],noise.inputs[0])
    l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
    l.new(noise.outputs['Fac'],b.inputs['Height']); l.new(b.outputs[0],p.inputs['Normal'])
    return m

plaster = textured('Warm aged plaster',(.42,.38,.29),(.71,.66,.52),scale=6,bump=.12)
green = textured('Faded sage wall',(.105,.18,.14),(.26,.34,.25),scale=4,bump=.09)
lower = textured('Lower wall warm grey',(.28,.27,.23),(.52,.48,.39),scale=8)
frame = material('Ivory painted window frames',(.65,.65,.53),.46)
metal = textured('Worn grey steel',(.23,.25,.22),(.46,.49,.42),scale=18,rough=.4,bump=.1)
metal.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.35
rubber = material('Dark rubber feet',(.022,.025,.024),.8)
wood = textured('Amber plywood grain',(.23,.12,.0614),(.60,.40,.17),(1,22,5),3,.39,.14)
edge = material('Plywood dark edge',(.25,.17,.087),.52)
boardmat = textured('Wiped dark green chalkboard',(.025,.075,.039),(.065,.145,.069),(1,1,1),7,.89,.065)
trim = material('Chalkboard stained timber',(.115,.081,.041),.48)
paper = material('Aged paper',(.76,.73,.59),.9)
blue = material('Corridor blue panels',(.075,.15,.185),.63)
cream = material('Curtain warm linen',(.72,.69,.56),.92)
red = textured('Red lacquer candy tin',(.17,.017,.012),(.55,.052,.028),scale=8,rough=.32,bump=.05)
silver = material('Tin folded silver rims',(.58,.58,.5),.26,.8)
label = material('Candy wrapper ivory',(.82,.76,.56),.57)
ink = material('Printed dark ink',(.058,.053,.039),.77)

def finish(o,name,mat):
    """Name an object, move it to current collection, assign material; return object."""
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    active_collection.objects.link(o)
    if mat: o.data.materials.append(mat)
    return o

def box(name, loc, size, mat, bevel=.008):
    """Add a cuboid with metre dimensions and optional physical bevel width."""
    # Direct mesh creation avoids a full dependency-graph update per small part.
    sx,sy,sz=(v*.5 for v in size)
    verts=[(-sx,-sy,-sz),(-sx,-sy,sz),(-sx,sy,-sz),(-sx,sy,sz),
           (sx,-sy,-sz),(sx,-sy,sz),(sx,sy,-sz),(sx,sy,sz)]
    faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces)
    o=bpy.data.objects.new(name,mesh);active_collection.objects.link(o);o.location=loc
    if mat:mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='UVMap')
    for face in mesh.polygons:
        axis=max(range(3),key=lambda a:abs(face.normal[a]))
        axes=[a for a in range(3) if a!=axis]
        for li in face.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]+loc[axes[0]],co[axes[1]]+loc[axes[1]])
    if bevel:
        mod=o.modifiers.new('Soft worn edges','BEVEL'); mod.width=bevel; mod.segments=3
    return o

def rod(name,a,b,r,mat):
    """Add a round tube between endpoints a/b, with radius r; return cylinder."""
    d=Vector(b)-Vector(a)
    # Model the final radius/depth directly so no transform operator is needed.
    verts=[(r*math.cos(i*math.tau/24),r*math.sin(i*math.tau/24),z*d.length*.5)
           for z in [-1,1] for i in range(24)]
    faces=[tuple(reversed(range(24))),tuple(range(24,48))]
    faces += [(i,(i+1)%24,(i+1)%24+24,i+24) for i in range(24)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces)
    o=bpy.data.objects.new(name,mesh);active_collection.objects.link(o)
    o.location=(Vector(a)+Vector(b))/2
    if mat:mesh.materials.append(mat)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    for p in o.data.polygons:p.use_smooth=p.index>1
    return o

def curve(name,points,r,mat):
    """Build a smooth poly tube from points; r is tube radius; return curve object."""
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.bevel_depth=r; d.bevel_resolution=2
    s=d.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,d); active_collection.objects.link(o); d.materials.append(mat)
    return o

def text_obj(name,body,loc,size,mat,rotation=(math.pi/2,0,0)):
    """Create flat text facing the rear camera by default, with given font size."""
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.align_y='CENTER'
    o=bpy.data.objects.new(name,d);active_collection.objects.link(o);o.location=loc;o.rotation_euler=rotation
    d.materials.append(mat);return o

# The enclosure deliberately has real window openings for sunlight and shadows.
box('Floor substrate',(0,-.7,-.10),(8.3,10.7,.18),edge)
box('Continuous scanned oak floor',(0,-.8,.008),(8.15,11.5,.025),wood,.001)
box('Front plaster wall',(0,4.6,1.8),(8.3,.2,3.6),green)
box('Front lower dado',(0,4.475,.55),(8.1,.05,1.1),lower)
box('Front dado rail',(0,4.41,1.1),(8.1,.09,.07),frame)
box('Ceiling',(0,-.65,3.65),(8.3,10.6,.16),plaster)
for x in [-4,4]:
    box('Window lower wall',(x,-.7,.51),(.18,10.5,1.02),lower)
    box('Window header',(x,-.7,3.45),(.2,10.5,.35),plaster)
    box('Window sill',(x,-.7,1.02),(.3,10.5,.095),frame)
    box('Skirting',(x-.03*(1 if x>0 else -1),-.7,.10),(.19,10.5,.16),trim)
    for y in [-5.85,-2.55,.8,4.35]:
        box('Structural window pier',(x,(0 if x<0 and y==.8 else y),1.9),(.27,(.6 if x<0 and y==.8 else .22),3.05),plaster)
    for y in [-5.65,-4.55,-3.45,-2.35,-1.25,-.15,.95,2.05,3.15,4.25]:
        box('Vertical window mullion',(x,y,2.16),(.11,.055,2.2),frame,.004)
    for z in ([1.10,2.70,3.25] if x<0 else [1.10,2.02,2.91,3.25]):
        box('Horizontal window transom',(x,-.7,z),(.12,10.3,.055),frame,.004)
    if x>0:
        for y in [-5.1,-4,-2.9,-1.8,-.7,.4,1.5,2.6,3.7]:
            box('Blue corridor clerestory',(4.02,y,3.075),(.035,1.03,.28),blue,.001)

# A corridor and distant pale massing supply a restrained cool view through glazing.
box('Corridor floor',(5.1,-.7,-.02),(2,10.6,.15),lower)
box('Corridor outer wall',(6.1,-.7,1.9),(.15,10.5,3.7),blue)
for y in [-4.3,-1.8,.7,3.2]:
    box('Corridor glazing bright',(6.0,y,2.2),(.03,2.0,1.7),material('Cool distant sky '+str(y),(.38,.50,.54),.85))
    for z in [1.4,2.1,3.0]:box('Corridor rails',(5.93,y,z),(.06,2.1,.04),metal)
for y in [4.3]:
    box('Ceiling beam',(0,y,3.46),(8.1,.16,.28),plaster)

# Chalkboard, tray, teacher's podium, old television and shelves.
active_collection=props
box('Chalkboard outer frame',(.45,4.28,2.10),(4.3,.15,1.66),trim,.026)
box('Chalkboard green face',(.45,4.185,2.10),(4.14,.035,1.49),boardmat,.006)
box('Chalk and eraser tray',(.45,4.09,1.31),(4.35,.24,.045),frame)
for x in [-1.6,-.8,.3,1.8]:box('Small chalk stick',(x,4.02,1.35),(.075,.012,.013),paper,.004)
box('Eraser',(1.65,4.035,1.36),(.17,.07,.04),trim)
box('Podium cabinet',(.45,3.14,.56),(1.18,.58,1.12),lower,.025)
box('Podium top',(.45,3.08,1.15),(1.30,.72,.055),wood,.018)
box('Teacher table',(1.75,3.25,.77),(1.15,.66,.05),wood)
for x in [1.25,2.25]:
    for y in [3.0,3.5]:rod('Teacher table leg',(x,y,.04),(x,y,.75),.025,metal)
box('Low equipment cabinet',(-3.12,4.03,.59),(1.1,.65,1.18),frame)
for x in [-3.4,-2.85]:
    box('Cabinet door',(x,3.684,.59),(.52,.025,1.09),plaster)
    rod('Cabinet pull',(x+.16,3.65,.52),(x+.16,3.65,.66),.012,metal)
box('CRT television shell',(-3.11,3.97,1.60),(.83,.57,.69),metal,.07)
screen=material('CRT dull glass',(.13,.17,.15),.22,.25)
box('CRT curved screen',(-3.15,3.656,1.64),(.67,.035,.49),screen,.065)
box('CRT lower panel',(-3.12,3.64,1.32),(.64,.045,.07),frame)
for x in [-2.93,-2.81]:rod('TV control',(x,3.64,1.33),(x,3.61,1.33),.017,rubber)
box('Bookshelf back',(-2.20,4.09,.73),(.64,.08,1.46),wood)
for x in [-2.55,-1.85]:box('Bookshelf upright',(x,3.9,.74),(.055,.5,1.48),wood)
for z in [.07,.52,1,1.47]:box('Bookshelf shelf',(-2.2,3.9,z),(.72,.5,.045),wood)
bookmats=[material('Book cover '+str(i),c,.75) for i,c in enumerate([(.2,.29,.29),(.45,.19,.11),(.58,.56,.37),(.09,.16,.23)])]
for i in range(10):
    ob=box('Shelf book',(-2.49+i*.06,3.86,1.18),(.045,.26,random.uniform(.26,.36)),random.choice(bookmats),.003)
    ob.rotation_euler.y=random.uniform(-.1,.1)
for i in range(5):box('Stacked exercise book',(-2.2,3.78,.57+i*.032),(.38,.28,.025),random.choice(bookmats),.002)

# Clock reads 4:35, with modelled hands and tick marks.
rod('Clock casing',(-1.75,4.31,3.17),(-1.75,4.20,3.17),.18,trim)
rod('Clock ivory face',(-1.75,4.19,3.17),(-1.75,4.18,3.17),.162,paper)
for k in range(12):
    a=k*math.tau/12
    rod('Clock tick',(-1.75+math.sin(a)*.139,4.163,3.17+math.cos(a)*.139),(-1.75+math.sin(a)*.152,4.163,3.17+math.cos(a)*.152),.003,ink)
rod('Minute hand',(-1.75,4.155,3.17),(-1.81,4.155,3.066),.004,ink)
rod('Hour hand',(-1.75,4.15,3.17),(-1.699,4.15,3.123),.006,ink)
for i in range(5):
    x=3.12+(i%3)*.29;z=2.2-(i//3)*.43
    box('Pinned school notice',(x,4.452,z),(.24,.008,.32),paper,.001)
    for j in range(5):box('Notice printed line',(x,4.442,z+.08-j*.03),(.15-random.random()*.05,.002,.006),metal,.0001)
box('Speaker cabinet',(2.52,4.26,3.1),(.32,.22,.28),lower)
for i in range(7):box('Speaker slit',(2.52,4.138,3.02+i*.023),(.23,.009,.006),ink,.001)

# Individual desks and chairs have rounded plywood and steel tube construction.
active_collection=furn

def curved_back(name,loc,width,height,depth,mat):
    """创建弧形胶合板椅背；输入中心、宽高厚与材质，返回带 UV 的实体网格。"""
    radius=.037;outline=[]
    for cx,cz,start in [(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,90),(-width/2+radius,-height/2+radius,180),(width/2-radius,-height/2+radius,270)]:
        for step in range(9):
            a=math.radians(start+step*90/8)
            outline.append((cx+radius*math.cos(a),cz+radius*math.sin(a)))
    n=len(outline)
    verts=[(x,side*depth/2+.030*(x/(width/2))**2,z) for side in [-1,1] for x,z in outline]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.materials.append(edge)
    for poly in mesh.polygons:
        if poly.index>1:poly.material_index=1
    uv=mesh.uv_layers.new(name='UVMap')
    for face in mesh.polygons:
        for li in face.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co.x+loc[0],co.z+loc[2])
    ob=bpy.data.objects.new(name,mesh);active_collection.objects.link(ob);ob.location=loc
    bevel=ob.modifiers.new('Laminated edge softness','BEVEL');bevel.width=.003;bevel.segments=3
    return ob

def desk_chair(index,x,y,angle):
    """Build one complete school desk/chair set at x/y, with a small layout rotation."""
    before=set(active_collection.objects)
    box('Desk %02d | edge'%index,(x,y,.735),(.9,.61,.047),edge,.025)
    box('Desk %02d | amber top'%index,(x,y,.761),(.885,.596,.024),wood,.023)
    box('Desk %02d | book tray'%index,(x,y+.015,.60),(.64,.40,.025),metal,.008)
    for sx in [-.31,.31]:
        box('Desk book tray side',(x+sx,y+.015,.655),(.018,.4,.11),metal,.004)
    box('Desk book tray rear',(x,y+.205,.655),(.64,.018,.11),metal,.004)
    for sx in [-.31,.31]:
        for sy in [-.22,.22]:
            rod('Desk tubular leg',(x+sx*1.09,y+sy*1.08,.04),(x+sx,y+sy,.719),.017,metal)
            rod('Desk rubber foot',(x+sx*1.09,y+sy*1.08,.005),(x+sx*1.09,y+sy*1.08,.04),.02,rubber)
        rod('Desk side stretcher',(x+sx,y-.23,.29),(x+sx,y+.23,.29),.013,metal)
    rod('Desk back stretcher',(x-.31,y+.22,.49),(x+.31,y+.22,.49),.014,metal)
    cy=y-.69
    box('Chair %02d | seat edge'%index,(x,cy,.433),(.44,.44,.027),edge,.026)
    box('Chair %02d | seat'%index,(x,cy,.453),(.43,.42,.025),wood,.027)
    for sx in [-.196,.196]:
        rod('Chair front leg',(x+sx*1.12,cy+.18,.024),(x+sx,cy+.15,.435),.015,metal)
        rod('Chair rear upright',(x+sx*1.14,cy-.22,.024),(x+sx,cy-.215,.86),.016,metal)
        rod('Chair side brace',(x+sx,cy-.20,.24),(x+sx,cy+.16,.24),.012,metal)
    # Curved top rail echoes the soft rounded silhouette in the photograph.
    pts=[(x-.218,cy-.22,.65),(x-.218,cy-.23,.85)]
    for step in range(9):
        a=math.pi-step*math.pi/16
        pts.append((x-.16+.058*math.cos(a),cy-.23,.85+.058*math.sin(a)))
    pts.append((x+.16,cy-.23,.908))
    for step in range(9):
        a=math.pi/2-step*math.pi/16
        pts.append((x+.16+.058*math.cos(a),cy-.23,.85+.058*math.sin(a)))
    pts.append((x+.218,cy-.22,.65))
    curve('Chair rounded back frame',pts,.019,metal)
    back=curved_back('Chair %02d | plywood back'%index,(x,cy-.225,.785),.390,.225,.032,wood)
    back.rotation_euler.x=math.radians(6)
    for sx in [-.154,.154]:rod('Chair back rivet',(x+sx,cy-.251,.8),(x+sx,cy-.26,.8),.008,silver)
    rod('Chair lower crossbar',(x-.2,cy-.21,.19),(x+.2,cy-.21,.19),.012,metal)
    # Apply each set's local rotation around its desktop centre.
    parts=set(active_collection.objects)-before
    for o in parts:
        d=o.location-Vector((x,y,0));c=math.cos(angle);s=math.sin(angle)
        o.location=(x+d.x*c-d.y*s,y+d.x*s+d.y*c,d.z)
        o.rotation_euler.z+=angle
    root=bpy.data.objects.new(f'asset_desk_set_{index:02d}',None)
    active_collection.objects.link(root);root.location=(x,y,0);root.empty_display_size=.15
    for o in parts:
        o.parent=root;o.location-=Vector((x,y,0));o['asset_set']=index

idx=0
for row,y in enumerate([-5.05,-3.35,-1.65,.05,1.70]):
    for col,x in enumerate([-2.85,-1.42,.05,1.53,2.98]):
        idx+=1
        if row==1 and col==0:
            desk_chair(idx,-1.95,-2.96,0)
            continue
        if row==1 and col==1:continue
        desk_chair(idx,x+random.uniform(-.09,.09),y+random.uniform(-.10,.10),random.uniform(-.075,.075))

# Draped linen curtains: sinusoidal folds gather tightly around a tie at mid-height.
active_collection=curt
def curtain(y0,width):
    """Create gathered curtain at left wall, centred on y0, with a given top width."""
    vs=[];fs=[];nu=20;nv=30
    for j in range(nv+1):
        z=.99+2.3*j/nv
        gather=1-.72*math.exp(-((z-1.8)/.33)**2)
        for i in range(nu+1):
            u=i/nu
            y=y0+(u-.5)*width*gather+.09*math.sin(j/nv*math.pi)
            x=-3.82+.057*math.sin(u*math.tau*5)*(0.7+.3*gather)
            vs.append((x,y,z+.027*math.sin(u*math.tau*3)*(1-j/nv)))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;fs.append((a,a+1,a+nu+2,a+nu+1))
    me=bpy.data.meshes.new('Linen folds');me.from_pydata(vs,[],fs);me.materials.append(cream)
    o=bpy.data.objects.new('Gathered linen curtain',me);active_collection.objects.link(o)
    uv=me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi=me.loops[li].vertex_index
            uv.data[li].uv=((vi%(nu+1))/nu*width,(vi//(nu+1))/nv*2.3)
    for p in me.polygons:p.use_smooth=True
    mod=o.modifiers.new('Cloth thickness','SOLIDIFY');mod.thickness=.003
    curve('Curtain tie',[(-3.75,y0-.10,1.8),(-3.71,y0+.04,1.78),(-3.77,y0+.16,1.8)],.015,cream)
for y in [-5.65,-2.55,.35,4.2]:curtain(y,.48)
rod('Curtain rail',(-3.77,-5.9,3.33),(-3.77,4.4,3.33),.019,frame)

# Fluorescent ceiling fittings are off; the principal light is the afternoon sun.
active_collection=props
tube=material('Fluorescent tube unlit',(.78,.78,.68),.34)
for x in [-2.35,0,2.35]:
    for y in [-3.2,.1,3.05]:
        box('Ceiling light housing',(x,y,3.47),(.26,1.3,.07),frame)
        for dx in [-.075,.075]:rod('Fluorescent tube',(x+dx,y-.58,3.405),(x+dx,y+.58,3.405),.023,tube)

# Small red tins approximate the seated fragmentary figure seen in the reference.
active_collection=candy
def tin(loc,scale=.12):
    """Create one red candy tin with ivory label and silver rims; return its parent."""
    parent=bpy.data.objects.new('Candy tin group',None);active_collection.objects.link(parent)
    parent.location=loc;parent.rotation_euler=[random.uniform(-.75,.75) for _ in range(3)]
    parts=[box('Red lacquered metal tin',(0,0,0),(scale,scale*.60,scale*1.15),red,.007),
           box('Ivory printed header',(0,-scale*.305,scale*.385),(scale*.94,.0015,scale*.27),label,.001)]
    for z in [-scale*.57,scale*.57]:
        parts.append(box('Silver pressed end plate',(0,0,z),(scale*1.01,scale*.615,.004),silver,.002))
        # 卷边采用细圆截面，保留独立几何而不把整张顶盖做成粗框。
        pts=[]
        for cx,cy,start_angle in [(scale*.43,scale*.23,0),(-scale*.43,scale*.23,90),(-scale*.43,-scale*.23,180),(scale*.43,-scale*.23,270)]:
            for j in range(6):
                a=math.radians(start_angle+j*90/5);pts.append((cx+scale*.07*math.cos(a),cy+scale*.07*math.sin(a),z))
        pts.append(pts[0]);parts.append(curve('Rolled seam',pts,.0017,silver))
    parts.append(rod('Tin circular lid',(scale*.19,0,scale*.575),(scale*.19,0,scale*.61),scale*.20,silver))
    ring=[(math.cos(j*math.tau/48)*scale*.33,-scale*.313,-scale*.11+math.sin(j*math.tau/48)*scale*.33) for j in range(49)]
    parts.append(curve('Ivory fine emblem',ring,scale*.012,label))
    parts.append(text_obj('Tin header typography','D R O P S',(0,-scale*.318,scale*.39),scale*.115,ink))
    parts.append(text_obj('Tin emblem typography','fruit',(0,-scale*.32,-scale*.12),scale*.12,label))
    for p in parts:p.parent=parent
    return parent

tin_centres=[]
def cluster(a,b,count,radius):
    """沿身体段生成有最小间距的罐体；输入端点、数量、横向半径，返回成功数。"""
    placed=0
    for attempt in range(count*160):
        v=Vector(a).lerp(Vector(b),random.random())
        v+=Vector((random.uniform(-radius,radius),random.uniform(-radius*.85,radius*.85),random.uniform(-radius*.4,radius*.4)))
        if any((v-q).length<.082 for q in tin_centres):continue
        ob=tin(v,random.uniform(.083,.112))
        ob.rotation_euler=[random.uniform(-1.1,1.1) for _ in range(3)]
        tin_centres.append(v);placed+=1
        if placed==count:break
    return placed

# 坐姿骨架：髋部落在椅面上，膝盖朝 +Y，双臂向桌面延伸。
cx,cy=-1.95,-3.65
cluster((cx,cy,.60),(cx-.05,cy+.06,1.20),55,.165)
cluster((cx-.06,cy+.06,1.32),(cx-.035,cy+.075,1.51),22,.133)
cluster((cx-.04,cy+.065,1.18),(cx-.04,cy+.07,1.34),9,.066)
for dx in [-.19,.19]:
    cluster((cx+dx,cy+.02,1.15),(cx+dx*1.3,cy+.27,.86),13,.065)
    cluster((cx+dx*1.3,cy+.27,.86),(cx+dx*1.15+.18,cy+.50,.84),12,.061)
for dx in [-.13,.15]:
    cluster((cx+dx,cy,.53),(cx+dx+.22,cy+.24,.48),15,.066)
    cluster((cx+dx+.22,cy+.24,.48),(cx+dx+.22,cy+.27,.12),14,.061)
    cluster((cx+dx+.23,cy+.28,.07),(cx+dx+.38,cy+.32,.07),6,.036)

# Camera and light: physical low sun crosses the room from the left windows.
active_collection=lights
def light(name,kind,loc,energy,color,target,size=None):
    """Add and aim a light; size sets area width or sun angular diameter."""
    d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=color
    o=bpy.data.objects.new(name,d);active_collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    if kind=='AREA':d.shape='DISK';d.size=size or 5
    if kind=='SUN':d.angle=size or .02
    return o
light('lgt_sun_afternoon','SUN',(-10,0,6),7.5,(1,.71,.33),(0,9.0,3.8),.014)
light('Large soft window sky','AREA',(-4.5,-.8,2.7),230,(.73,.83,1),(0,.4,1.2),6)
light('Cool corridor bounce','AREA',(3.8,.3,2.5),45,(.52,.7,1),(0,0,1.1),4)
world=bpy.data.worlds.new('Faint blue sky');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(.48,.61,.76,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.13
# Keep the visible exterior bright while preserving restrained sky fill indoors.
wn,wl=world.node_tree.nodes,world.node_tree.links
visible_sky=wn.new('ShaderNodeBackground');visible_sky.inputs[0].default_value=(.81,.86,.88,1)
visible_sky.inputs[1].default_value=1.5
ray=wn.new('ShaderNodeLightPath');mix=wn.new('ShaderNodeMixShader')
wl.new(ray.outputs['Is Camera Ray'],mix.inputs[0])
wl.new(wn.get('Background').outputs[0],mix.inputs[1]);wl.new(visible_sky.outputs[0],mix.inputs[2])
wl.new(mix.outputs[0],wn.get('World Output').inputs[0])
scene.world=world
active_collection=collection('cam_sh010')
camdata=bpy.data.cameras.new('Classroom 24 mm');cam=bpy.data.objects.new('cam_sh010_main',camdata)
active_collection.objects.link(cam);cam.location=(.4,-7.5,1.25)
cam.rotation_euler=(Vector((0,4.3,.87))-cam.location).to_track_quat('-Z','Y').to_euler()
camdata.lens=24;camdata.sensor_width=36;scene.camera=cam
camdata.dof.use_dof=True;camdata.dof.focus_distance=6;camdata.dof.aperture_fstop=8

# Render settings favour a clean, reproducible still without external assets.
scene.render.engine='CYCLES';scene.cycles.samples=384;scene.cycles.use_denoising=True
scene.cycles.max_bounces=7
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    gpu=False
    for dev in prefs.devices:
        dev.use=dev.type!='CPU';gpu=gpu or dev.use
    if gpu:scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=2560;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
RENDER=ROOT/f'04_renders/sq010/sh010/beauty/{VERSION}/drop_sq010_sh010_beauty_{VERSION}.png'
RENDER.parent.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(RENDER)
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.65
scene.render.film_transparent=False



# 前侧教室门与深色门玻璃，减少右侧没有结构的纯亮区域。
active_collection=arch
box('Right front classroom door',(3.91,3.35,1.30),(.12,1.12,2.6),frame,.015)
box('Door frosted blue glass',(3.83,3.35,1.79),(.018,.82,1.04),blue,.008)
box('Door lower inset',(3.83,3.35,.60),(.02,.84,.98),lower,.008)
rod('Door pull',(3.77,2.94,.97),(3.77,2.94,1.16),.014,metal)
box('Front baseboard',(0,4.43,.10),(8.1,.07,.15),trim,.004)
# 窗外远楼仅提供尺度和柔和色块，不替代主要参考构图。
exterior=material('Distant weathered concrete',(.39,.44,.42),.9)
for y in [-5,-1,3]:
    box('Distant school block',(-9.5,y,-.2),(1.0,2.9,2.35),exterior,.01)
    for z in [.15,.65]:
        box('Distant building band',(-8.97,y,z),(.03,2.8,.055),frame,.002)

# 接入已校验的 CC0 扫描贴图；UV 以米为单位，所有路径最终转为工程相对路径。
def scanned(mat, asset_id, tile=1.0, tint=None, strength=.35):
    """将素材清单中的扫描图接入 mat；tile 为 UV 重复尺寸（米），tint 可选色调。"""
    manifest=json.loads((ROOT/'00_admin/asset_manifest.json').read_text(encoding='utf-8'))
    asset=next(a for a in manifest['assets'] if a['id']==asset_id)
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    p=nodes.get('Principled BSDF')
    for socket in ['Base Color','Roughness','Normal']:
        for link in list(p.inputs[socket].links):links.remove(link)
    uv=nodes.new('ShaderNodeTexCoord');uv.location=(-900,0)
    mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=1/tile;mapping.location=(-700,0)
    links.new(uv.outputs['UV'],mapping.inputs[0])
    for f in asset['files']:
        path=ROOT/f['path'];name=path.name.lower();channel=f.get('channel','')
        if channel not in ['diff','rough','nor_gl']:
            if '_color.' in name:channel='diff'
            elif '_roughness.' in name:channel='rough'
            elif '_normalgl.' in name:channel='nor_gl'
            else:continue
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
        tex.image.colorspace_settings.name='sRGB' if channel=='diff' else 'Non-Color'
        tex.label=asset_id+' / '+channel;tex.location=(-450,200-['diff','rough','nor_gl'].index(channel)*240)
        links.new(mapping.outputs[0],tex.inputs['Vector'])
        if channel=='diff':
            if tint:
                mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1)
                links.new(tex.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],p.inputs['Base Color'])
            else:links.new(tex.outputs['Color'],p.inputs['Base Color'])
        elif channel=='rough':links.new(tex.outputs['Color'],p.inputs['Roughness'])
        else:
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=strength
            links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs[0],p.inputs['Normal'])
    mat['source_asset']=asset_id;mat['uv_tile_metres']=tile

floor_mat=material('mat_floor_scanned_oak',(.25,.15,.07))
scanned(floor_mat,'old_wooden_floor_03',1.2,strength=.5)
scene.objects['Continuous scanned oak floor'].data.materials[0]=floor_mat
fp=floor_mat.node_tree.nodes.get('Principled BSDF')
fp.inputs['Coat Weight'].default_value=.28
fp.inputs['Coat Roughness'].default_value=.22
scanned(wood,'plywood',1.1,tint=(.91,.77,.55),strength=.18)
wp=wood.node_tree.nodes.get('Principled BSDF')
wp.inputs['Coat Weight'].default_value=.16
wp.inputs['Coat Roughness'].default_value=.3
scanned(plaster,'painted_plaster_wall',2.0,tint=(.72,.68,.55),strength=.3)
scanned(green,'painted_plaster_wall',2.0,tint=(.21,.32,.23),strength=.3)
scanned(lower,'painted_plaster_wall',2.0,tint=(.57,.54,.45),strength=.3)
scanned(cream,'Fabric030',.6,tint=(.85,.78,.62),strength=.22)
cp=cream.node_tree.nodes.get('Principled BSDF')
# 原扫描为深色织物；保留其纤维法线与粗糙度，重新染成参考的奶白色。
for link in list(cp.inputs['Base Color'].links):cream.node_tree.links.remove(link)
cp.inputs['Base Color'].default_value=(.68,.63,.50,1)
cp.inputs['Sheen Weight'].default_value=.22

scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.fps=24;scene.frame_start=1001;scene.frame_end=1001;scene.frame_set(1001)
scene.render.image_settings.color_depth='16'
scene['reference']='https://www.bilibili.com/video/BV18V411f7Qf/'
scene['notes']='Single-frame reconstruction study; camera and dimensions inferred. CC0 scanned PBR sources in asset_manifest.json.'
scene['production_version']=VERSION
scene['delivery_scope']='Editable single-frame study; no source animation recreation.'
scene.camera.data.passepartout_alpha=1.0
# 删除此后台进程自带的空默认场景，保留唯一正式镜头。
for other in list(bpy.data.scenes):
    if other!=scene:bpy.data.scenes.remove(other)
source=bpy.data.texts.load(str(Path(__file__)))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
            area.spaces.active.region_3d.view_camera_zoom=12
            area.spaces.active.region_3d.view_camera_offset=(0,0)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.filepath=bpy.path.relpath(image.filepath,start=str(BLEND.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print('SHOT_READY',VERSION,len(scene.objects),'objects',flush=True)
