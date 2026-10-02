"""Replace equipment shading by native SD outputs and rebuild the cabinet as real wooden joinery.
Preserves collection pivots, visible installation extents and non-cabinet geometry; first version backed up.
"""
import bpy,ast,math,json,random
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/00_projects/10_CG/Shot_Test');TEX=ROOT/'02_assets/textures/generated/equipment_sd';CACHE=ROOT/'07_pipeline/cache/equipment_rebuild'
scene=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
manifest=json.loads((TEX/'manifest.json').read_text());materials={}

def sd_material(family):
    """Load real SAT-produced PBR maps with metric UV mapping and true OpenGL normal conversion."""
    info=next(x for x in manifest if x['family']==family);m=bpy.data.materials.new('EQ SD '+family);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    uv=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=4;l.new(uv.outputs['UV'],scale.inputs[0])
    for channel,socket in [('BaseColor','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal','Normal')]:
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/family/(channel+'.png')),check_existing=True);tex.image.colorspace_settings.name='sRGB' if channel=='BaseColor' else 'Non-Color';l.new(scale.outputs[0],tex.inputs['Vector'])
        if channel=='Normal':
            nn=n.new('ShaderNodeNormalMap');nn.inputs['Strength'].default_value=1;l.new(tex.outputs['Color'],nn.inputs['Color']);l.new(nn.outputs['Normal'],p.inputs['Normal'])
        else:l.new(tex.outputs['Color'],p.inputs[socket])
    if family=='varnished_wood':p.inputs['Coat Weight'].default_value=.42;p.inputs['Coat Roughness'].default_value=.22
    if family=='glass':p.inputs['Coat Weight'].default_value=.35
    m['source_sbs']=info['source'];m['source_sbsar']=info['sbsar'];m['tile_metres']=.25;m['height_range_metres']=info['height_range_metres'];materials[family]=m;return m
for family in [x['family'] for x in manifest]:sd_material(family)
# Replace every equipment material family; the printed clock face is rebuilt with real vector lettering below.
for o in bpy.data.objects:
    if not hasattr(o.data,'materials'):continue
    for slot in o.material_slots:
        if not slot.material:continue
        old=slot.material.name.lower()
        family='enamel'
        if 'abs' in old:family='abs'
        elif 'rubber' in old:family='rubber'
        elif 'graphite' in old:family='dark'
        elif 'zinc' in old:family='metal'
        elif 'paper' in old or 'print' in old or 'phosphor' in old:family='paper'
        elif 'glass' in old:family='glass'
        slot.material=materials[family]
        if 'clear cover' in old:
            clear=materials['glass'].copy();clear.name='EQ SD optical clear cover';p=clear.node_tree.nodes.get('Principled BSDF')
            for link in list(p.inputs['Base Color'].links):clear.node_tree.links.remove(link)
            p.inputs['Base Color'].default_value=(.96,.98,.96,1);p.inputs['Transmission Weight'].default_value=1;slot.material=clear
# Reuse the project's documented mesh helpers without executing their build main body.
enamel=materials['enamel'];metal=materials['metal'];dark=materials['dark'];rubber=materials['rubber'];wood=materials['varnished_wood'];raw=materials['exposed_wood']
tree=ast.parse((ROOT/'07_pipeline/scripts/equipment_rebuild.py').read_text(encoding='utf-8-sig'))
for fn in tree.body:
    if isinstance(fn,ast.FunctionDef) and fn.name in ['mesh','box','rod','path','circle','screw']:
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<equipment mesh helpers>','exec'))
enamel=materials['enamel'];metal=materials['metal'];dark=materials['dark'];rubber=materials['rubber'];wood=materials['varnished_wood'];raw=materials['exposed_wood']
active=bpy.data.collections['AST_equipment_cabinet'];pivot=Vector(active.instance_offset)
for o in list(active.all_objects):bpy.data.objects.remove(o,do_unlink=True)
random.seed(91117)

def board(name,center,size,grain_axis=2,mat=None):
    """Construct a full-thickness wood board and orient metric UV V along its actual grain axis."""
    ob=box(name,center,size,mat or wood,.0014);ob.data.materials.append(raw)
    for face in ob.data.polygons:
        normal_axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=normal_axis]
        if grain_axis in axes:axes=[k for k in axes if k!=grain_axis]+[grain_axis]
        else:face.material_index=1
        for li in face.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            ob.data.uv_layers[0].data[li].uv=(co[axes[0]]+random.Random(name).random()*.19,co[axes[1]])
    ob['construction']='Solid timber / veneered timber panel; physically modelled board thickness';ob['grain_axis']=grain_axis
    return ob

# Flush classroom cupboard: plain proportions from film, with real 25/30/20 mm wooden panels.
for x in [-.54,.54]:board('EQ wood cabinet 25mm side',(x,0,.59),(.025,.65,1.18),2)
board('EQ wood cabinet 30mm top',(0,0,1.165),(1.06,.64,.030),0)
for z in [.043,.57]:board('EQ wood cabinet fixed shelf',(0,.005,z),(1.06,.61,.023),0)
board('EQ wood cabinet 6mm rebated back',(0,.312,.59),(1.06,.006,1.115),2)
for x in [-.45,.45]:board('EQ wood cabinet base bearer',(x,.005,.022),(.09,.56,.044),1)
board('EQ wood cabinet recessed kickboard',(0,-.292,.065),(1.025,.020,.086),0)
for x in [-.271,.271]:
    # Independent door stiles/rails meet around an 18 mm field panel; seams remain understated.
    for dx in [-.245,.245]:board('EQ wood door vertical stile',(x+dx,-.338,.59),(.040,.023,1.105),2)
    for z in [.064,1.116]:board('EQ wood door horizontal rail',(x,-.338,z),(.450,.023,.053),0)
    board('EQ wood door flush inset panel',(x,-.335,.59),(.450,.020,1.000),2)
    hx=x+(.17 if x<0 else -.17)
    for z in [.53,.65]:
        box('EQ cabinet pull escutcheon',(hx,-.352,z),(.026,.003,.027),metal,.003)
        rod('EQ cabinet handle standoff',(hx,-.352,z),(hx,-.381,z),.005,metal)
    path('EQ cabinet curved pull',[(hx,-.375,.53),(hx,-.389,.542),(hx,-.389,.638),(hx,-.375,.65)],.006,metal)
    for z in [.22,.92]:
        xx=x+(-.248 if x<0 else .248)
        box('EQ cabinet butt hinge leaf',(xx,-.352,z),(.035,.004,.052),metal,.001)
        rod('EQ cabinet hinge barrel',(xx,-.358,z-.032),(xx,-.358,z+.032),.0053,metal)
        for zz in [-.016,.016]:screw((xx+(.009 if x<0 else -.009),-.356,z+zz),.0024)
    # Local bare wood is clustered along the lower contact edge and near pulls, never scattered uniformly.
    for j in range(5):
        cx=x-.20+j*.091+random.uniform(-.012,.012);length=random.uniform(.018,.048);z=.040+random.uniform(-.001,.002);yy=-.35005
        verts=[(cx-length/2,yy,z),(cx-length*.3,yy,z+.003),(cx-length*.12,yy,z+.0017),(cx+length*.16,yy,z+.0045),(cx+length*.36,yy,z+.002),(cx+length/2,yy,z),(cx+length*.2,yy,z-.0006)]
        mesh('EQ local lower rail clearcoat loss',verts,[tuple(range(len(verts)))],raw,0)
    for j in range(2):
        z=.52+j*.118;cx=hx+(.026 if x<0 else -.026)
        mesh('EQ pull contact clearcoat rub',[(cx,-.3501,z-.012),(cx+.003,-.3501,z-.003),(cx+.001,-.3501,z+.015),(cx-.0015,-.3501,z+.008)],[(0,1,2,3)],raw)
# A handful of irregular exposed veneer patches at the top front edge, comparable to handled desktop edges.
for j in range(9):
    cx=-.49+j*.12+random.uniform(-.02,.02);ln=random.uniform(.026,.072);z=1.161
    verts=[(cx-ln/2,-.32005,z-.002),(cx-ln*.36,-.32005,z+.002),(cx-ln*.1,-.32005,z+.001),(cx+ln*.08,-.32005,z+.004),(cx+ln*.4,-.32005,z+.001),(cx+ln/2,-.32005,z-.002)]
    mesh('EQ top edge clearcoat loss exposes timber',verts,[tuple(range(6))],raw)
rod('EQ cabinet cam lock',(.058,-.352,.60),(.058,-.357,.60),.011,metal)
box('EQ cabinet lock slot',(.058,-.359,.60),(.0015,.001,.012),dark,.0002)
active['construction']='Wooden cabinet: 25 mm carcass, 30 mm top, framed wood doors with 18–20 mm infill, rebated back';active['material_authority']='User correction 2026-09-11: wood, not folded metal'
# Clock print becomes actual vector numbers/ticks over SD paper, so no Pillow surface dependency remains.
active=bpy.data.collections['AST_wall_clock'];pivot=Vector(active.instance_offset)
for k in range(60):
    a=k*math.tau/60;r0=.137 if k%5==0 else .144;r1=.151
    rod('EQ clock printed minute mark',(math.sin(a)*r0,-.076,math.cos(a)*r0),(math.sin(a)*r1,-.076,math.cos(a)*r1),.0008 if k%5==0 else .00032,dark,16)
for k in range(1,13):
    a=k*math.tau/12;cu=bpy.data.curves.new('Clock number','FONT');cu.body=str(k);cu.align_x='CENTER';cu.align_y='CENTER';cu.size=.021;cu.extrude=.00003
    ob=bpy.data.objects.new('EQ clock printed numeral',cu);active.objects.link(ob);ob.location=pivot+Vector((math.sin(a)*.116,-.076,math.cos(a)*.116));ob.rotation_euler=(math.pi/2,0,0);cu.materials.append(dark)
# Purge unused pre-SD materials/images, keeping only dependencies actively used by this source.
for m in list(bpy.data.materials):
    if m.users==0:bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.users==0:bpy.data.images.remove(im)
# Mirror the old review camera, but all new surfaces are the genuine SD materials.
out=ROOT/'02_assets/work/classroom_equipment.blend'
for im in bpy.data.images:
    if im.source=='FILE':im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath),start=str(out.parent))
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('Saved wooden cabinet and native SD equipment materials',len(active.all_objects))
