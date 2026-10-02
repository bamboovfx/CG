"""只读课椅替换前场景：集合实例、旧椅几何、相机／动画及可用姿态。"""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'07_pipeline/cache/chair_scene_replace_20261001'


def object_record(ob):
    """输入场景对象，返回类型／实例／变换及网格范围，避免只按名称推断旧椅。"""
    r={'name':ob.name,'type':ob.type,'matrix':[list(row) for row in ob.matrix_world],
       'collections':[c.name for c in ob.users_collection],
       'instance':ob.instance_collection.name if ob.instance_collection else None,
       'parent':ob.parent.name if ob.parent else None}
    if ob.type=='MESH':
        r.update(vertices=len(ob.data.vertices),bounds=[list(ob.matrix_world@Vector(v)) for v in ob.bound_box],
                 materials=[m.name if m else None for m in ob.data.materials])
    return r


def main():
    """输入当前教室磁盘工程，输出替换边界检查；不修改对象。"""
    sc=bpy.context.scene
    records=[object_record(o) for o in bpy.data.objects]
    data={'file':bpy.data.filepath,'scene':sc.name,'frame':sc.frame_current,
          'camera':sc.camera.name if sc.camera else None,'frame_start':sc.frame_start,
          'frame_end':sc.frame_end,'fps':sc.render.fps,'objects':records,
          'collections':[{'name':c.name,'objects':[o.name for o in c.objects],
                          'children':[a.name for a in c.children],'offset':list(c.instance_offset)} for c in bpy.data.collections],
          'actions':[a.name for a in bpy.data.actions]}
    WORK.mkdir(parents=True,exist_ok=True)
    (WORK/'shot_inspect.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SHOT_INSPECT '+json.dumps({'scene':sc.name,'objects':len(records),'collections':len(bpy.data.collections),
       'chairs':[r['name'] for r in records if 'chair' in r['name'].lower() or 'chair' in str(r['instance']).lower()]}),flush=True)


if __name__=='__main__':
    main()
