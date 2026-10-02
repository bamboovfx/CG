"""一次有界的静态坐姿修正：固定 Root/环境，使用刚性身体段，不逐罐拼图。

输入已保存的 camera reveal baseline；输出独立 pose_fit_candidate 和三张灰模。
保持原片表演仍待制作的状态，不修改完整视频或正式镜头。
"""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/sh010_blocking_20260920'
CACHE=ROOT/'07_pipeline/cache/sh010_blocking_20260920'
DEST=CACHE/'pose_fit_candidate.blend'
GROUPS=ROOT/'06_review/production_audit_20260920/character/body_groups.json'
groups={g['body_part']:g for g in json.loads(GROUPS.read_text(encoding='utf-8'))['groups']}
scene=bpy.context.scene
assert Path(bpy.data.filepath).name=='drop_sq010_sh010_blocking.blend'
scene.frame_set(1140)
bpy.context.view_layer.update()
original={o.name:o.matrix_world.copy() for o in scene.objects if o.library is None}
pivot=Vector((-1.95,-2.5625,.53))
head_proxy=Vector((-1.995,-2.50,1.63))
target=np.array([375.,450.])


def project(point):
    """输入世界点；返回原片1920×1080含黑边坐标。"""
    p=world_to_camera_view(scene,scene.camera,Vector(point))
    return np.array([p.x*1920,132+(1-p.y)*816])


def torso_matrix(angles):
    """输入前倾/侧倾弧度；返回围绕固定骨盆的刚体变换。"""
    return Matrix.Translation(pivot)@Matrix.Rotation(float(angles[0]),4,'X')@Matrix.Rotation(float(angles[1]),4,'Y')@Matrix.Translation(-pivot)


angles=np.radians(np.array([-22.,-4.]))
for _ in range(20):
    error=project(torso_matrix(angles)@head_proxy)-target
    jac=np.column_stack([(project(torso_matrix(angles+np.eye(2)[i]*.001)@head_proxy)-target-error)/.001 for i in range(2)])
    step=np.linalg.lstsq(jac,error,rcond=None)[0]
    proposed=np.clip(angles-step,np.radians([-30,-10]),np.radians([0,10]))
    if np.linalg.norm(proposed-angles)<.0001:
        break
    angles=proposed
body=torso_matrix(angles)
for name in ['torso','neck','head']:
    ctrl=bpy.data.objects['ctrl_tin_'+name]
    ctrl.matrix_basis=body@ctrl.matrix_basis


def frame_at(a,b):
    """输入身体段端点；返回与原控制架一致的无缩放坐标架。"""
    y=(Vector(b)-Vector(a)).normalized()
    x=Vector((1,0,0))-y*y.x
    x.normalize()
    z=x.cross(y).normalized()
    m=Matrix((x,y,z)).transposed().to_4x4()
    m.translation=Vector(a)
    return m


def bend(a,b,l1,l2,pole):
    """输入链端点/两段长度/弯曲方向；返回保长关节点和超伸误差。"""
    axis=(b-a).normalized()
    distance=(b-a).length
    used=min(distance,l1+l2-.001)
    t=(l1*l1-l2*l2+used*used)/(2*used)
    h=math.sqrt(max(0.,l1*l1-t*t))
    normal=pole-axis*pole.dot(axis)
    normal.normalize()
    return a+axis*t+normal*h,distance-l1-l2


def length(name):
    """输入身体段名；返回来源段的固定长度。"""
    g=groups[name]
    return (Vector(g['rest_end'])-Vector(g['rest_start'])).length


def segment(name,a,b):
    """输入身体段和新端点；设置控制器，罐体仍保持刚性。"""
    bpy.data.objects['ctrl_tin_'+name].matrix_basis=frame_at(a,b)


# 两脚整体收回有限距离并把原始最低点抬到地面；膝用两段 IK 跟随。
foot_shift=Vector((-.205,-.168,0))
joint_errors=[]
for side,label in [(-1,'minus_x'),(1,'plus_x')]:
    foot=groups['foot_'+label]
    move=foot_shift.copy()
    move.z=.0205-foot['raw_bounds'][0][2]
    fctrl=bpy.data.objects['ctrl_tin_foot_'+label]
    fctrl.matrix_basis=Matrix.Translation(move)@fctrl.matrix_basis
    thigh=groups['thigh_'+label]
    shin=groups['shin_'+label]
    hip=Vector(thigh['rest_start'])
    ankle=Vector(shin['rest_end'])+move
    knee,reach=bend(hip,ankle,length('thigh_'+label),length('shin_'+label),Vector((0,1,0)))
    segment('thigh_'+label,hip,knee)
    segment('shin_'+label,knee,ankle)
    joint_errors.append({'limb':'leg_'+label,'overreach_m':reach,
                         'segment_length_error_m':[abs((knee-hip).length-length('thigh_'+label)),abs((ankle-knee).length-length('shin_'+label))]})
    # 手收回桌沿附近，肘落在身体前下方；此静态pose不能替代后续抬手表演。
    upper=groups['upper_arm_'+label]
    shoulder=body@Vector(upper['rest_start'])
    hand=Vector((pivot.x+side*.15,pivot.y+.31,.85))
    elbow,reach=bend(shoulder,hand,length('upper_arm_'+label),length('forearm_'+label),Vector((side*.2,-.8,-.7)))
    segment('upper_arm_'+label,shoulder,elbow)
    segment('forearm_'+label,elbow,hand)
    joint_errors.append({'limb':'arm_'+label,'overreach_m':reach,
                         'segment_length_error_m':[abs((elbow-shoulder).length-length('upper_arm_'+label)),abs((hand-elbow).length-length('forearm_'+label))]})
bpy.context.view_layer.update()
others=[name for name,m in original.items() if not name.startswith(('tin_','ctrl_tin_'))
        and max(abs(bpy.data.objects[name].matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))>1e-5]
assert not others
assert max(abs(bpy.data.objects['ctrl_tin_root'].matrix_world[r][c]-original['ctrl_tin_root'][r][c]) for r in range(4) for c in range(4))<1e-7
result={'candidate':str(DEST),'baseline_preserved':str(CACHE/'drop_sq010_sh010_blocking.blend'),
        'static_pose_only':True,'full_video_uses_baseline_not_pose_fit':True,
        'torso_pitch_side_degrees':np.degrees(angles).tolist(),
        'head_proxy_before_xy':project(head_proxy).tolist(),'head_proxy_after_xy':project(body@head_proxy).tolist(),
        'head_proxy_target_xy':target.tolist(),'foot_shift_xy_m':list(foot_shift)[:2],
        'joint_checks':joint_errors,'other_objects_changed':others,'root_fixed':True,
        'limits':['Head coordinate is a proxy, actual can silhouette must be inspected.',
                  'Static folded arm pose does not replace observed end-of-shot arm extension.',
                  'Foot AABB lowest point placed on plane; no exact collision test performed.']}
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),relative_remap=True,compress=True)
(OUT/'pose_fit_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.render_aa='8'
scene.render.resolution_x=1280
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.use_compositing=False
scene.render.use_sequencer=False
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
for frame in [1001,1071,1140]:
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'pose_fit_{frame}.png')
    bpy.ops.render.render(write_still=True)
print('POSE_FIT_ONE_PASS_FINISHED',json.dumps(result),flush=True)
