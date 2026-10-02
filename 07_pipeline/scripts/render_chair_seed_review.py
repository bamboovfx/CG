"""从候选取三把实际椅子进行一致三点光Seed对照；临时评审不写回场景灯光与摆位。"""
from pathlib import Path
import sys
import bpy
from mathutils import Matrix

sys.path.insert(0,str(Path(__file__).resolve().parent))
from replace_scene_chairs import OUT
from wood_layers_blender import aim


def main():
    """输入可编辑场景候选，输出三把椅子的同光种子对照图；退出前不保存临时设置。"""
    sc=bpy.context.scene
    roots=[bpy.data.objects[n] for n in ['asset_desk_set_01_chair','asset_desk_set_02_chair','asset_desk_set_03_chair']]
    for ob in sc.objects:ob.hide_render=True
    for index,root in enumerate(roots):
        root.hide_render=False
        root.matrix_world=Matrix.Translation(((index-1)*.59,0,.0205))@Matrix.Diagonal((1.1231344,1.1231344,1.1231344,1))
        for ob in root.children:ob.hide_render=False
    world=bpy.data.worlds.new('REVIEW / studio');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.12,.12,.12,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
    sc.world=world
    for name,pos,power,size in [('Key',(1.7,2.3,3.0),650,2.5),('Fill',(-2,1.3,2.0),350,3),('Rim',(0,-2,2.5),500,2)]:
        data=bpy.data.lights.new('REVIEW / '+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new('REVIEW / '+name,data);sc.collection.objects.link(ob);ob.location=pos;aim(ob,(0,0,.45))
    bpy.ops.mesh.primitive_plane_add(size=200)
    plane=bpy.context.object;plane.name='REVIEW / floor'
    plane.location.z=.0205  # Match the classroom's existing controller ground datum for this studio-only comparison.
    mat=bpy.data.materials.new('REVIEW / floor');mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.17,.17,.17,1);bsdf.inputs['Roughness'].default_value=.85
    plane.data.materials.append(mat)
    camera=bpy.data.objects.new('REVIEW / seed comparison',bpy.data.cameras.new('REVIEW / seed comparison'))
    sc.collection.objects.link(camera);camera.location=(1.35,2.85,1.55);aim(camera,(0,0,.45));camera.data.lens=53;sc.camera=camera
    sc.view_settings.exposure=0;sc.render.resolution_x=1500;sc.render.resolution_y=950;sc.render.resolution_percentage=100
    sc.cycles.samples=24;sc.cycles.seed=177;sc.render.image_settings.color_depth='8'
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    sc.cycles.device='GPU';sc.render.filepath=str(OUT/'seed_variants.png')
    bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
    print('SEED_VARIANTS_RENDERED',flush=True)


if __name__=='__main__':
    main()
