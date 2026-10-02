"""按污斑UV定位实际木板表面，再以同光紧特写验证；只渲染，不保存工程。"""
from pathlib import Path
import sys
import json
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wood_layers_blender import aim
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'06_review/tripo_wood_dirt_20260930'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930/tripo_wood_dirt.blend'))
ob=bpy.data.objects['LP_part_02']; mesh=ob.data; uv=mesh.uv_layers['UV_WoodReference']


def locate(u,v):
    """输入目标UV，返回相应顶面三角形上的世界坐标；避免凭猜测选错特写区域。"""
    mesh.calc_loop_triangles()
    for tri in mesh.loop_triangles:
        # Tripo对象有旋转，顶面判定使用世界法线，不使用局部Z。
        if (ob.matrix_world.to_3x3()@tri.normal).z<.5: continue
        loops=list(tri.loops); a,b,c=[uv.data[l].uv for l in loops]
        d=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
        if abs(d)<1e-10: continue
        wa=((b.y-c.y)*(u-c.x)+(c.x-b.x)*(v-c.y))/d
        wb=((c.y-a.y)*(u-c.x)+(a.x-c.x)*(v-c.y))/d; wc=1-wa-wb
        if min(wa,wb,wc)<-1e-5: continue
        p=sum((mesh.vertices[mesh.loops[l].vertex_index].co*w for l,w in zip(loops,[wa,wb,wc])),Vector())
        return ob.matrix_world@p
    raise RuntimeError('Requested dirt UV did not hit top surface')


target=locate(.225,.79)
sc=bpy.context.scene; prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'; prefs.get_devices()
for d in prefs.devices: d.use=d.type=='OPTIX'
sc.cycles.device='GPU'; sc.cycles.samples=128; sc.cycles.seed=930
sc.camera.location=target+Vector((.035,-.07,.115)); sc.camera.data.lens=95; aim(sc.camera,target)
sc.render.resolution_x=sc.render.resolution_y=2000; sc.render.image_settings.color_depth='16'
controls=[next(n for n in bpy.data.objects[name].data.materials[0].node_tree.nodes if n.get('wood_layers_role')=='surface_dirt') for name in ['LP_part_02','LP_part_09']]
for strength,filename in ([(1,'08_stain_after')] if '--after-only' in sys.argv else [(0,'07_stain_before'),(1,'08_stain_after')]):
    for c in controls: c.inputs['Dirt'].default_value=strength
    sc.render.filepath=str(OUT/(filename+'.png')); bpy.ops.render.render(write_still=True)
    print('DIRT_CLOSEUP '+filename,flush=True)
(OUT/'stain_closeup.json').write_text(json.dumps({'uv':[.225,.79],'world':list(target),'lens':95,'resolution':2000,'lights_unchanged':True},indent=2),encoding='utf-8')
