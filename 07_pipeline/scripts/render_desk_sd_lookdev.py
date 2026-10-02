"""Render Adobe-generated desk materials in a separate Cycles lookdev scene.

Inputs: final 4K PBR channels, 20 cm UV tile, OpenGL tangent normals.
Outputs: shader preview blend and raking-light detail renders. Desk source is untouched.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
TEX=ROOT/'02_assets/textures/generated/school_desk_sd'
OUT=ROOT/'06_review/sd_material'
OUT.mkdir(parents=True,exist_ok=True)


def aim(ob,target):
    """Point a camera/light's negative Z axis toward a world-space target."""
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


def material(family):
    """Build a physically scaled PBR material from one Substance preset."""
    mat=bpy.data.materials.new('SD_Desk_'+family); mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    p=nodes.get('Principled BSDF'); p.location=(200,120)
    for i,(ch,port) in enumerate([('BaseColor','Base Color'),('Roughness','Roughness'),('Metallic','Metallic'),('Normal',None)]):
        tex=nodes.new('ShaderNodeTexImage'); tex.location=(-520,350-i*260)
        tex.label=f'{ch} | native 4K | 20 cm tile'
        tex.image=bpy.data.images.load(str(TEX/family/'4k'/f'{ch}.png'),check_existing=True)
        tex.image.colorspace_settings.name='sRGB' if ch=='BaseColor' else 'Non-Color'
        tex.interpolation='Linear'
        if port: links.new(tex.outputs['Color'],p.inputs[port])
        else:
            n=nodes.new('ShaderNodeNormalMap'); n.location=(-80,-300)
            n.inputs['Strength'].default_value=1
            n.label='OpenGL | physical height range 0.6 mm'
            links.new(tex.outputs['Color'],n.inputs['Color']); links.new(n.outputs['Normal'],p.inputs['Normal'])
    mat.asset_mark(); mat.asset_data.description='Native SD desk enamel: 20 cm tile, 4K channels, independent steel and oxide.'
    return mat


def sheet():
    """Create a subtly crowned 20 cm sheet with physical UV scale for highlight inspection."""
    n=64; verts=[]; faces=[]
    for j in range(n+1):
        for i in range(n+1):
            x=(i/n-.5)*.2; y=(j/n-.5)*.2
            verts.append((x,y,.004*(x/.1)**2))
    for j in range(n):
        for i in range(n):
            k=j*(n+1)+i; faces.append((k,k+1,k+n+2,k+n+1))
    mesh=bpy.data.meshes.new('physical_20cm_sheet'); mesh.from_pydata(verts,[],faces)
    uv=mesh.uv_layers.new(name='Physical_20cm')
    for poly in mesh.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            co=verts[mesh.loops[li].vertex_index]; uv.data[li].uv=(co[0]/.2+.5,co[1]/.2+.5)
    ob=bpy.data.objects.new('Enamel over pressed steel | 200 mm',mesh); bpy.context.collection.objects.link(ob)
    mod=ob.modifiers.new('Sheet thickness 1.2 mm','SOLIDIFY'); mod.thickness=.0012
    bevel=ob.modifiers.new('Rolled corner highlight','BEVEL'); bevel.width=.0004; bevel.segments=3
    return ob


def light(name,loc,power,size,color,target=(0,0,0),shape='DISK',size_y=None):
    """Create a named area light; dimensions and power stay fixed across both presets."""
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape=shape; data.size=size; data.color=color
    if size_y is not None: data.size_y=size_y
    ob=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(ob); ob.location=loc; aim(ob,target)
    return ob


def render(name,target,width,loc_offset):
    """Render a measured field of view without depth-of-field or denoising blur."""
    cam=bpy.context.scene.camera; cam.location=Vector(target)+Vector(loc_offset); aim(cam,target)
    cam.data.ortho_scale=width
    bpy.context.scene.render.filepath=str(OUT/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('LOOKDEV_RENDERED',name,flush=True)


def main():
    """Build only a new preview scene, then render identical lighting for each preset."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=192; sc.cycles.use_denoising=False
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    sc.cycles.device='GPU'; sc.render.resolution_x=1440; sc.render.resolution_y=1440; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_depth='16'
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
    sc.render.film_transparent=False
    world=bpy.data.worlds.new('Neutral studio'); world.use_nodes=True; sc.world=world
    world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.25
    # One long softbox gives a clean reflection gradient and reveals micro-normal breakup.
    light('Grazing strip softbox',(-.12,.14,.10),1.2,.23,(1,.94,.85),shape='RECTANGLE',size_y=.025)
    light('Soft fill',(.16,-.08,.25),.35,.18,(.82,.9,1))
    data=bpy.data.cameras.new('Measured material camera'); cam=bpy.data.objects.new('Measured material camera',data)
    bpy.context.collection.objects.link(cam); sc.camera=cam; data.type='ORTHO'; data.clip_start=.001; data.clip_end=10
    ob=sheet(); mats={family:material(family) for family in ['frame','brace']}
    for family,mat in mats.items():
        ob.data.materials.clear(); ob.data.materials.append(mat)
        render(f'{family}_surface',(0,0,0),.24,(.015,-.12,.31))
        render(f'{family}_macro_60mm',(.035,.025,.0005),.06,(.012,-.055,.22))
    ob.data.materials.clear(); ob.data.materials.append(mats['frame'])
    dest=ROOT/'02_assets/materials/school_desk/desk_material_lookdev.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(dest))


if __name__=='__main__':
    main()
