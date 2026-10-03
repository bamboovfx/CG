"""管线评审实验：比较链接数据与本地数据，保留集合实例，不改正式镜头。"""
import bpy,json,time,sys,ctypes,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/pipeline_review_20260929';OUT.mkdir(parents=True,exist_ok=True)
CACHE=ROOT/'07_pipeline/cache/pipeline_review_20260929'
mode=sys.argv[sys.argv.index('--')+1]


def memory():
    """返回Windows当前进程工作集/私有提交内存MiB，不当作GPU显存。"""
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage']]
    c=Counters();c.cb=ctypes.sizeof(c)
    kernel=ctypes.windll.kernel32;kernel.GetCurrentProcess.restype=ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(kernel.GetCurrentProcess()),ctypes.byref(c),c.cb)
    return {'working_set_MiB':c.WorkingSetSize/1048576,'private_MiB':c.PrivateUsage/1048576}


def stats():
    """统计实际载入数据、共享关系和实例；不把文件大小当作性能。"""
    s=bpy.context.scene
    return {'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'images':len(bpy.data.images),
      'vertices':sum(len(m.vertices) for m in bpy.data.meshes),'polygons':sum(len(m.polygons) for m in bpy.data.meshes),
      'scene_objects':len(s.objects),'instances':dict(Counter(o.instance_collection.name for o in s.objects if o.instance_collection)),
      'mesh_sharing_histogram':dict(Counter(Counter(o.data.as_pointer() for o in bpy.data.objects if o.type=='MESH').values())),
      'linked_objects':sum(o.library is not None for o in bpy.data.objects),'linked_materials':sum(m.library is not None for m in bpy.data.materials),'memory':memory()}


if mode=='prepare':
    before=stats()
    # ALL本地化保留数据共享；禁止Make Instances Real及逐实例复制网格。
    bpy.ops.object.make_local(type='ALL');bpy.context.view_layer.update()
    after=stats()
    protect=['objects','meshes','materials','images','vertices','polygons','scene_objects','instances','mesh_sharing_histogram']
    diff={k:[before[k],after[k]] for k in protect if before[k]!=after[k]}
    assert not diff,diff
    board=bpy.data.objects['Unique wiped writing surface']
    assert board.active_material.is_editable and board.active_material.node_tree.is_editable
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/'local_candidate.blend'),relative_remap=True)
    (OUT/'localization.json').write_text(json.dumps({'before':before,'after':after,'differences':diff,'board_editable':True},indent=2),encoding='utf8')
    print('LOCALIZATION_OK')
else:
    r=stats();s=bpy.context.scene
    # 相同种子/光照/帧，只改小样渲染设置；不保存测试相机或输出设置。
    s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.seed=123
    s.render.resolution_x=640;s.render.resolution_y=270;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.filepath=str(OUT/(mode+'.png'))
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU';s.render.use_persistent_data=False
    start=time.perf_counter();bpy.ops.render.render(write_still=True);r['render_wall_seconds']=time.perf_counter()-start
    r['after_render_memory']=memory();r['file_bytes']=Path(bpy.data.filepath).stat().st_size
    r['frame']=s.frame_current;r['resolution']=[640,270];r['samples']=16
    (OUT/(mode+'.json')).write_text(json.dumps(r,indent=2),encoding='utf8')
    print('BENCHMARK_RESULT',json.dumps(r))
