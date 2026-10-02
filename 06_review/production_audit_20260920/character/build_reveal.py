"""基于原片量化 guide 建立静根部 140 帧 camera reveal 候选。

仅写 cache 候选：保留坐姿、167 罐链接、其他资产和原材质，不添加无证据的步行。
拟合点为已有几何的对应近似点；输出残差，不能冒充原片相机解算。
"""
import bpy
import json
import math
import hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
AUDIT=Path(__file__).resolve().parent
CACHE=ROOT/'07_pipeline/cache/sh010_blocking_20260920'
REVIEW=ROOT/'06_review/sh010_blocking_20260920'
CACHE.mkdir(parents=True,exist_ok=True)
REVIEW.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
DEST=CACHE/'drop_sq010_sh010_blocking.blend'
scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==SOURCE.resolve()
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
original={o.name:o.matrix_world.copy() for o in scene.objects if o.library is None}
camera=scene.camera
saved_camera={'location':list(camera.location),'rotation':list(camera.rotation_euler),'lens':camera.data.lens}
groups=json.loads((AUDIT/'body_groups.json').read_text(encoding='utf-8'))['groups']
guide=json.loads((AUDIT.parent/'hero_motion_guide.json').read_text(encoding='utf-8'))


def control(name,role):
    """输入名称和用途；返回可编辑本地 Empty，控制器初始不改变坐姿。"""
    o=bpy.data.objects.new(name,None)
    rig.objects.link(o)
    o.empty_display_type='PLAIN_AXES'
    o.empty_display_size=.14
    o['blocking_role']=role
    return o


def frame_at(a,b):
    """输入静态身体段端点；返回右手坐标架以保留每罐的世界矩阵。"""
    y=(Vector(b)-Vector(a)).normalized()
    x=Vector((1,0,0))-y*y.x
    x.normalize()
    z=x.cross(y).normalized()
    m=Matrix((x,y,z)).transposed().to_4x4()
    m.translation=Vector(a)
    return m


def rotation(pitch,yaw):
    """输入 Euler X/Z 弧度；返回无 roll 的相机旋转矩阵。"""
    c,s=math.cos(pitch),math.sin(pitch)
    a,b=math.cos(yaw),math.sin(yaw)
    return np.array([[a,-b*c,b*s],[b,a*c,-a*s],[0,s,c]])


def project(params,point):
    """输入相机参数和世界点；返回1920×1080原片含黑边坐标及正深度。"""
    x,y,z,pitch,yaw,lens=params
    q=rotation(pitch,yaw).T@(np.array(point)-params[:3])
    d=-q[2]
    f=1920*lens/36
    return np.array([960+f*q[0]/d,132+(405-f*q[1]/d)*816/810]),d


# 对应点的物理位置来自当前资产，端点定义存在误差，明确保留拟合残差。
landmarks=[
    ('clock',[-1.75,4.20,3.17],[811,282],1.0),
    ('board_outer_top_right',[2.60,4.15,2.90],[1256,318],1.0),
    ('chair_back_top_right',[-1.669,-2.77,.8943],[378,653],.8),
    ('head_top_approx',[-1.995,-2.50,1.63],[375,450],.4),
    ('foot_contact_approx',[-1.72,-2.26,.0205],[408,918],.4),
]


def residual(params):
    """输入拟合参数；返回特征点加权误差及前后景视差比例误差。"""
    errors=[]
    depths=[]
    for name,point,target,weight in landmarks:
        actual,depth=project(params,point)
        errors.extend((actual-np.array(target))*weight)
        depths.append(depth)
    errors.append((depths[0]/depths[2]-308/79)*60)
    return np.array(errors)


params=np.array([*camera.location,camera.rotation_euler.x,camera.rotation_euler.z,camera.data.lens],dtype=float)
lower=np.array([-2,-9,.7,1.30,-.3,15])
upper=np.array([2,-4,2.5,1.75,.3,40])
for iteration in range(80):
    error=residual(params)
    jac=np.column_stack([(residual(params+np.eye(6)[j]*.0001)-error)/.0001 for j in range(6)])
    step=np.linalg.lstsq(jac,error,rcond=None)[0]
    for scale in [1,.5,.25,.1,.03]:
        trial=np.clip(params-step*scale,lower,upper)
        if np.linalg.norm(residual(trial))<np.linalg.norm(error):
            params=trial
            break
    else:
        break

# 控制层的 rest 姿势与正式场景逐对象校验；没有身体关键帧。
rig=bpy.data.collections.new('chr_tin_blocking_controls')
scene.collection.children.link(rig)
root=control('ctrl_tin_root','Fixed seated root; source motion does not justify travel')
rest={}
for group in groups:
    c=control('ctrl_tin_'+group['body_part'],group['body_part'])
    c.parent=root
    rest_frame=frame_at(group['rest_start'],group['rest_end'])
    c.matrix_basis=rest_frame
    for name in group['instances']:
        o=bpy.data.objects[name]
        world=original[name]
        rest[name]={'matrix_world':[list(row) for row in world],'body_part':group['body_part']}
        o.parent=c
        o.matrix_parent_inverse=Matrix.Identity(4)
        o.matrix_basis=rest_frame.inverted()@world
        o['body_part']=group['body_part']
        o['blocking_status']='Preserved seated rest; local motion not yet matched'

camera.location=tuple(params[:3])
camera.rotation_euler=(params[3],0,params[4])
camera.data.lens=float(params[5])
end_location=camera.location.copy()
right=Vector(rotation(params[3],params[4])[:,0])
depth=project(params,landmarks[0][1])[1]
travel=guide['observed_camera_image_change']['mean_front_wall_dx_px']*depth/(1920*params[5]/36)
for f in [1001,1140]:
    u=(f-1001)/139
    camera.location=end_location+right*travel*(1-u)
    camera.keyframe_insert('location',frame=f)
for layer in camera.animation_data.action.layers:
    for strip in layer.strips:
        for slot in camera.animation_data.action.slots:
            bag=strip.channelbag(slot)
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation='LINEAR'
scene.frame_start=1001
scene.frame_end=1140
scene.render.fps=24
scene.render.fps_base=1
scene['blocking_stage']='Static seated-root camera reveal; approximate projection fit; local arm/head action pending'
scene.frame_set(1140)
bpy.context.view_layer.update()
transform_error={name:max(abs(bpy.data.objects[name].matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))
                 for name,m in original.items() if name!=camera.name}
assert max(transform_error.values())<1e-5
fit=[]
for name,point,target,weight in landmarks:
    actual,d=project(params,point)
    fit.append({'point':name,'world_point':point,'end_actual_source_pixels':actual.tolist(),'end_reference_source_pixels':target,
                'error_pixels':(actual-target).tolist(),'full_travel_pixels':1920*params[5]/36*travel/d})
for im in bpy.data.images:
    if im.library is None and im.source=='FILE' and im.filepath:
        im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath),start=str(DEST.parent))
for lib in bpy.data.libraries:
    lib.filepath=bpy.path.relpath(bpy.path.abspath(lib.filepath),start=str(DEST.parent))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),relative_remap=False,compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report={'mode':'camera_reveal_static_root','candidate':str(DEST),'source_hash':source_hash,'source_unchanged':True,
        'frames':[1001,1140],'fps':24,'duration_seconds':140/24,'source_camera':saved_camera,
        'candidate_end_camera':{'location':list(end_location),'rotation':list(camera.rotation_euler),'lens':camera.data.lens},
        'camera_travel_right_to_left_m':travel,'character_controls':len(groups)+1,'character_actions':0,
        'max_preserved_object_world_matrix_error':max(transform_error.values()),'fit_landmarks':fit,
        'reference_guide':str(AUDIT.parent/'hero_motion_guide.json'),
        'limits':['Not an original-film camera solve; asset proportions differ.',
                  'No walking or root travel; local upper-body animation still pending reference match.',
                  'Point correspondences are approximate and errors are retained.',
                  'Original user camera only changed in candidate; canonical source unchanged.']}
(CACHE/'reveal_parameters.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(CACHE/'rest_pose.json').write_text(json.dumps(rest,ensure_ascii=False,indent=2),encoding='utf-8')
(REVIEW/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CAMERA_REVEAL_SAVED',str(DEST),flush=True)
print('FIT',json.dumps(fit),flush=True)
