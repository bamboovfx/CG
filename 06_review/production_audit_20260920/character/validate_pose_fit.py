"""只读重开姿态候选，验证依赖并记录几何投影；包围盒不替代遮挡分割。"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/sh010_blocking_20260920'
report=json.loads((OUT/'pose_fit_report.json').read_text(encoding='utf-8'))
baseline=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
scene=bpy.context.scene
missing=[bpy.path.abspath(im.filepath,library=im.library) for im in bpy.data.images
         if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath,library=im.library)).exists()]
source_hash=hashlib.sha256((ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend').read_bytes()).hexdigest()
assert source_hash==baseline['source_hash'] and not missing


def points(ob):
    """输入罐体实例；返回所有原始零件包围盒的世界顶点，供保守投影。"""
    result=[]
    c=ob.instance_collection
    base=ob.matrix_world@Matrix.Translation(-c.instance_offset)
    for part in c.all_objects:
        if part.type in {'MESH','CURVE','FONT'}:
            result.extend(base@part.matrix_world@Vector(v) for v in part.bound_box)
    return result


def project(point):
    """输入世界点；返回原片像素坐标，未计算家具遮挡。"""
    p=world_to_camera_view(scene,scene.camera,point)
    return [float(p.x*1920),float(132+(1-p.y)*816)]


scene.frame_set(1140)
bpy.context.view_layer.update()
heads=[p for ob in scene.objects if ob.get('body_part')=='head' for p in points(ob)]
feet=[p for ob in scene.objects if str(ob.get('body_part','')).startswith('foot_') for p in points(ob)]
head_uv=[project(v) for v in heads]
top=min(head_uv,key=lambda p:p[1])
foot_contact=Vector(((min(p.x for p in feet)+max(p.x for p in feet))/2,
                     (min(p.y for p in feet)+max(p.y for p in feet))/2,
                     min(p.z for p in feet)))
report.update({'reopened_validation':True,'missing_images':missing,'canonical_source_hash_unchanged':True,
               'head_projected_bounds_top_xy':top,'head_bounds_top_error_xy':[top[0]-375,top[1]-450],
               'foot_bbox_contact_proxy_world':list(foot_contact),'foot_bbox_contact_proxy_xy':project(foot_contact),
               'foot_proxy_error_xy':[project(foot_contact)[0]-408,project(foot_contact)[1]-918],
               'projection_note':'Bounds projection ignores occlusion and bevels; it is not pixel segmentation. Exact proxy fit does not mean the silhouette is exact.'})
(OUT/'pose_fit_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('POSE_VALIDATION',json.dumps(report),flush=True)
