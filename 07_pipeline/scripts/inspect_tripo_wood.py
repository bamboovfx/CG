"""只读检查Tripo木板的局部轴、尺寸与UV；输出用于材质映射的JSON。"""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_baked.blend'
OUT=ROOT/'07_pipeline/cache/tripo_wood_reference_20260930'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
items=[]
for name in ('LP_part_02','LP_part_09'):
    # 局部轴继承FBX导入旋转；记录世界角点避免投影方向猜测。
    ob=bpy.data.objects[name]
    items.append({'name':name,'matrix':[list(row) for row in ob.matrix_world],
        'bounds_local':[list(p) for p in ob.bound_box],
        'bounds_world':[list(ob.matrix_world@Vector(p)) for p in ob.bound_box],
        'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),
        'uv':[u.name for u in ob.data.uv_layers],
        'custom_normals':ob.data.has_custom_normals,
        'materials':[m.name if m else None for m in ob.data.materials]})
result={'source':str(SOURCE),'boards':items,'objects':[o.name for o in bpy.context.scene.objects if o.type=='MESH']}
(OUT/'input_inspection.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
