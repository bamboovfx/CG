"""在候选文件建立 167 罐刚性分段步态；不覆盖任何正式 Blender 文件。

输入：正式镜头和已核验的 body_groups.json；输出：候选、参数和验证数据。
动作是可调整的 blocking 制作设定，不声称已经逐帧匹配原片。
"""
raise RuntimeError('REJECTED hypothesis: source is camera reveal. Use build_reveal.py; never run this walking experiment.')
import bpy
import json
import math
import hashlib
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
AUDIT = Path(__file__).resolve().parent
CACHE = ROOT/'07_pipeline/cache/sh010_blocking_20260920'
REVIEW = ROOT/'06_review/sh010_blocking_20260920'
CACHE.mkdir(parents=True, exist_ok=True)
REVIEW.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT/'03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
DEST = CACHE/'drop_sq010_sh010_blocking.blend'
P = {'frame_start':1001,'frame_end':1140,'fps':24,
     'walk_start':1023,'walk_end':1140,'cycle_frames':32,'stance_fraction':.60,
     'pelvis_height':.742,'foot_height':.108,'foot_lift':.09,'step_width':.27,
     'path':[[-3.64,-5.20],[-3.63,-3.12],[-2.48,-2.80]],
     'path_corner_at':.72,'body_bob':.013,'arm_swing_radians':.25,
     'notes':'Initial approximate path; source motion guide pending. Candidate only. Camera preserved.'}
param_path = CACHE/'blocking_parameters.json'
if param_path.exists():
    P.update(json.loads(param_path.read_text(encoding='utf-8')))
else:
    param_path.write_text(json.dumps(P,ensure_ascii=False,indent=2),encoding='utf-8')
groups = json.loads((AUDIT/'body_groups.json').read_text(encoding='utf-8'))['groups']
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
scene = bpy.context.scene
assert Path(bpy.data.filepath).resolve() == SOURCE.resolve(), 'Must begin from canonical source, never rerun on candidate.'
original = {o.name:[list(row) for row in o.matrix_world] for o in scene.objects if o.library is None}
original_camera = scene.camera.matrix_world.copy()
original_parent = {o.name:o.parent.name if o.parent else None for o in scene.objects if o.library is None}
rig = bpy.data.collections.new('chr_tin_blocking_controls')
scene.collection.children.link(rig)


def empty(name, role):
    """输入名称和语义用途；返回本地可编辑控制器，不改变资产集合。"""
    o = bpy.data.objects.new(name,None)
    rig.objects.link(o)
    o.empty_display_type='ARROWS'
    o.empty_display_size=.12
    o['blocking_role']=role
    o.rotation_mode='QUATERNION'
    return o


def segment_frame(start, end, right=Vector((1,0,0))):
    """输入段端点和期望右轴；返回保持体积的正交段坐标架。"""
    y=(Vector(end)-Vector(start)).normalized()
    x=right-y*right.dot(y)
    if x.length<.05:
        alt=Vector((0,0,1))
        x=alt-y*alt.dot(y)
    x.normalize()
    z=x.cross(y).normalized()
    m=Matrix((x,y,z)).transposed().to_4x4()
    m.translation=Vector(start)
    return m


def smooth(t):
    """输入 0..1；返回零端点速度的三次插值系数。"""
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)


def path_at(frame):
    """输入可为小数的帧；返回路径位置、方向角及标准化进度。"""
    u=max(0.,min(1.,(frame-P['walk_start'])/(P['walk_end']-P['walk_start'])))
    a,b,c=[Vector((v[0],v[1],0)) for v in P['path']]
    corner=P['path_corner_at']
    # 二次 Bezier 在转角处平滑，避免角色横移时瞬间转身。
    t=u
    q=(1-t)**2*a+2*t*(1-t)*b+t*t*c
    tangent=2*(1-t)*(b-a)+2*t*(c-b)
    yaw=math.atan2(-tangent.x,tangent.y)
    return q,yaw,u


def foot_at(frame, side):
    """输入帧与 ±1 侧别；返回带固定支撑段的世界足踝目标和接触状态。"""
    cycle=P['cycle_frames']
    phase_offset=0 if side<0 else cycle/2
    elapsed=max(0.,frame-P['walk_start'])+phase_offset
    cycle_index=math.floor(elapsed/cycle)
    phase=(elapsed/cycle)-cycle_index
    begin=P['walk_start']+cycle_index*cycle-phase_offset
    stance=P['stance_fraction']
    def target(contact_frame):
        """输入支撑中心帧；返回路径上的足踝接触位置。"""
        p,yaw,_=path_at(contact_frame)
        p+=Matrix.Rotation(yaw,4,'Z')@Vector((side*P['step_width']/2,0,0))
        p.z=P['foot_height']
        return p
    first=target(begin+cycle*stance/2)
    if phase<stance:
        return first,True,phase
    t=(phase-stance)/(1-stance)
    second=target(begin+cycle+cycle*stance/2)
    result=first.lerp(second,smooth(t))
    result.z+=P['foot_lift']*math.sin(math.pi*t)
    return result,False,phase


def knee_at(hip,ankle,forward):
    """输入髋、踝和前方向；返回保留旧腿长的两骨 IK 膝点。"""
    l1=math.sqrt(.22**2+.24**2+.05**2)
    l2=math.sqrt(.03**2+.36**2)
    d=ankle-hip
    dist=d.length
    axis=d.normalized()
    reach=min(dist,l1+l2-.001)
    along=(l1*l1-l2*l2+reach*reach)/(2*reach)
    height=math.sqrt(max(.0001,l1*l1-along*along))
    pole=forward-axis*forward.dot(axis)
    pole.normalize()
    return hip+axis*along+pole*height,dist-(l1+l2)


def key(o,matrix,frame):
    """输入控制器局部矩阵与帧；插入可直接编辑的位置和四元数关键帧。"""
    o.matrix_basis=matrix
    o.keyframe_insert('location',frame=frame)
    o.keyframe_insert('rotation_quaternion',frame=frame)


root=empty('ctrl_tin_root','World path; all segment controls are children')
root['source_rest_pose']='seated; retained in rest_pose.json'
controls={}
rest={}
for g in groups:
    name=g['body_part']
    ctrl=empty('ctrl_tin_'+name,name)
    ctrl.parent=root
    controls[name]=ctrl
    frame=segment_frame(g['rest_start'],g['rest_end'])
    ctrl.matrix_world=frame
    for name_instance in g['instances']:
        ob=bpy.data.objects[name_instance]
        world=ob.matrix_world.copy()
        rest[name_instance]={'matrix_world':[list(r) for r in world],'body_part':name}
        ob.parent=ctrl
        ob.matrix_parent_inverse=Matrix.Identity(4)
        ob.matrix_basis=frame.inverted()@world
        ob['body_part']=name
        ob['blocking_status']='rigid segment attachment; not final simulation'
feet={side:empty('ctrl_tin_foot_target_'+str(side),'World contact target; baked per-frame') for side in [-1,1]}
metrics=[]
for f in range(P['frame_start'],P['frame_end']+1):
    base,yaw,u=path_at(f)
    rotation=Matrix.Rotation(yaw,4,'Z')
    right=rotation@Vector((1,0,0))
    forward=rotation@Vector((0,1,0))
    phase=(f-P['walk_start'])/P['cycle_frames']*math.tau
    moving=1 if P['walk_start']<=f<=P['walk_end'] else 0
    base.z=P['pelvis_height']+P['body_bob']*math.cos(2*phase)*moving
    root_m=rotation.copy()
    root_m.translation=base
    key(root,root_m,f)
    inv=root_m.inverted()
    def point(x,y,z):
        """输入骨盆局部点；返回当前角色方向下的世界点。"""
        return base+rotation@Vector((x,y,z))
    poses={
      'torso':(point(0,0,.07),point(-.05,.06,.67)),
      'neck':(point(-.04,.065,.65),point(-.04,.07,.81)),
      'head':(point(-.06,.06,.79),point(-.035,.075,.98)),
    }
    for side,label,hipx in [(-1,'minus_x',-.13),(1,'plus_x',.15)]:
        ankle,planted,footphase=foot_at(f,side)
        foot_m=Matrix.Translation(ankle)
        key(feet[side],foot_m,f)
        hip=point(hipx,0,0)
        knee,overreach=knee_at(hip,ankle,forward)
        poses['thigh_'+label]=(hip,knee)
        poses['shin_'+label]=(knee,ankle)
        heel=ankle+forward*.012+Vector((0,0,-.050))
        poses['foot_'+label]=(heel,heel+forward*math.sqrt(.15**2+.04**2))
        # 肩肘各自转动，前臂保留微弯；手端不再停留于静态桌面。
        shoulder=point(side*.19,.02,.62)
        swing=P['arm_swing_radians']*math.sin(phase+(math.pi if side>0 else 0))*moving
        upper_len=math.sqrt(.057**2+.25**2+.29**2)
        lower_len=math.sqrt((.18-side*.0285)**2+.23**2+.02**2)
        elbow=shoulder+forward*(math.sin(swing)*upper_len)+Vector((0,0,-math.cos(swing)*upper_len))
        hand=elbow+forward*(math.sin(swing+.25)*lower_len)+Vector((0,0,-math.cos(swing+.25)*lower_len))
        poses['upper_arm_'+label]=(shoulder,elbow)
        poses['forearm_'+label]=(elbow,hand)
        metrics.append({'frame':f,'side':side,'planted':planted,'ankle':list(ankle),'overreach':overreach})
    for name,(a,b) in poses.items():
        key(controls[name],inv@segment_frame(a,b,right),f)

# 每帧都有采样，使用线性曲线使接触段不会被自动 Bezier 切线带动。
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                try:
                    bag=strip.channelbag(slot)
                except Exception:
                    continue
                if bag:
                    for curve in bag.fcurves:
                        for point_key in curve.keyframe_points:
                            point_key.interpolation='LINEAR'
scene.frame_start=P['frame_start']
scene.frame_end=P['frame_end']
scene.render.fps=P['fps']
scene.render.fps_base=1
scene['blocking_stage']='Candidate rigid segment gait; requires motion/path/occlusion review'
scene.frame_set(P['frame_start'])
bpy.context.view_layer.update()
assert all(abs(scene.camera.matrix_world[r][c]-original_camera[r][c])<1e-6 for r in range(4) for c in range(4))
nonchar=[]
for name,m in original.items():
    if name.startswith('tin_'):
        continue
    ob=bpy.data.objects[name]
    if max(abs(ob.matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))>1e-5:
        nonchar.append(name)
assert not nonchar, nonchar
# 路径以候选位置重定位，只改内存中的库地址；源文件保持原字节。
for library in bpy.data.libraries:
    library.filepath=bpy.path.abspath(library.filepath)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),relative_remap=True,compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
(CACHE/'rest_pose.json').write_text(json.dumps(rest,ensure_ascii=False,indent=2),encoding='utf-8')
(REVIEW/'contact_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
(REVIEW/'build_report.json').write_text(json.dumps({'source_hash':source_hash,'source_unchanged':True,'candidate':str(DEST),
    'frames':[scene.frame_start,scene.frame_end],'fps':scene.render.fps,'animated_controls':len(controls)+3,
    'instances':len(rest),'other_transforms_changed':nonchar,'camera_unchanged':True,
    'max_leg_overreach_m':max(v['overreach'] for v in metrics)},ensure_ascii=False,indent=2),encoding='utf-8')
print('BLOCKING_CANDIDATE_SAVED',str(DEST),flush=True)
