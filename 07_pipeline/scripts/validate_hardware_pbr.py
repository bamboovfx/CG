"""验证真实候选：UV拉伸/重叠、纹理读回、固定三角化、用户变换与非目标对象保护。"""
import bpy
import sys
import json
import hashlib
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from audit_hardware_uv import inspect_uv, audit

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/window_hardware_pbr'
CACHE=ROOT/'07_pipeline/cache/window_hardware_pbr'


def snapshot():
    """输入当前建筑场景，输出可比较的全部对象变换/层级及非目标数据引用。"""
    return {o.name:{'matrix':[[round(x,6) for x in row] for row in o.matrix_world],
                    'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,
                    'mods':[[m.name,m.type] for m in o.modifiers]} for o in bpy.context.scene.objects}


def overlap_and_bounds(objects, resolution=2048):
    """在UV三角形内部采样栅格，检查不同三角形面积重叠；边界不计入，避免共边误报。"""
    occupancy=np.zeros((resolution,resolution),np.uint16); outside=0
    for ob in objects:
        me=ob.data; me.calc_loop_triangles(); layer=me.uv_layers.active.data
        for tri in me.loop_triangles:
            xy=np.array([layer[i].uv[:] for i in tri.loops])*resolution
            if xy.min() < -1e-4 or xy.max()>resolution+1e-4: outside+=1
            x0,y0=np.maximum(0,np.floor(xy.min(axis=0)).astype(int)); x1,y1=np.minimum(resolution,np.ceil(xy.max(axis=0)).astype(int))
            if x1<=x0 or y1<=y0: continue
            d1,d2=xy[1]-xy[0],xy[2]-xy[0]; denom=d1[0]*d2[1]-d1[1]*d2[0]
            if abs(denom)<1e-10: continue
            yy,xx=np.mgrid[y0:y1,x0:x1]; p=np.stack([xx+.5-xy[0,0],yy+.5-xy[0,1]],axis=-1)
            a=(p[...,0]*(xy[2,1]-xy[0,1])-p[...,1]*(xy[2,0]-xy[0,0]))/denom
            b=((xy[1,0]-xy[0,0])*p[...,1]-(xy[1,1]-xy[0,1])*p[...,0])/denom
            occupancy[y0:y1,x0:x1]+=((a>1e-5)&(b>1e-5)&(a+b<1-1e-5)).astype(np.uint16)
    return {'resolution':resolution,'overlapping_interior_pixels':int((occupancy>1).sum()),
            'outside_triangles':outside,'uv_coverage':float((occupancy>0).mean())}


def validate(label):
    """输入候选/发布标签；检查真实资产并写JSON，失败返回明确指标。"""
    manifest=json.loads((OUT/'build_manifest.json').read_text(encoding='utf-8'))
    before=json.loads((OUT/'source_fingerprint.json').read_text(encoding='utf-8')); after=snapshot()
    names={n for r in manifest['groups'] for n in r['targets']}
    transformed=[n for n,b in before.items() if n not in after or b['matrix']!=after[n]['matrix'] or b['parent']!=after[n]['parent']]
    other=[n for n,b in before.items() if n not in names and b!=after.get(n)]
    representatives=[bpy.data.objects[r['targets'][0]] for r in manifest['groups']]
    metrics=[inspect_uv(o) for o in representatives]; atlas=overlap_and_bounds(representatives)
    textures={}
    # 从磁盘重新加载纹理，确认交付文件有效，不仅是内存里能渲染。
    for key,meta in manifest['textures'].items():
        path=ROOT/'02_assets/textures/window_hardware'/(key+'.png'); img=bpy.data.images.load(str(path),check_existing=False)
        img.colorspace_settings.name='sRGB' if key=='BaseColor' else 'Non-Color'
        pixels=np.empty(len(img.pixels),np.float32); img.pixels.foreach_get(pixels)
        rgb=pixels.reshape((-1,4))[:,:3]
        textures[key]={'size':list(img.size),'min':float(rgb.min()),'max':float(rgb.max()),'finite':bool(np.isfinite(rgb).all()),
                       'sha256_match':hashlib.sha256(path.read_bytes()).hexdigest()==meta['sha256']}
        bpy.data.images.remove(img)
    mapping=audit()
    triangulated=all(len(p.vertices)==3 for o in representatives for p in o.data.polygons)
    good=not transformed and not other and all(m['collapsed']==0 and m['stretch_p95']<1.25 for m in metrics)
    good=good and atlas['outside_triangles']==0 and atlas['overlapping_interior_pixels']==0 and triangulated and mapping['passed']
    good=good and all(t['size']==[4096,4096] and t['finite'] and t['sha256_match'] for t in textures.values())
    report={'file':bpy.data.filepath,'passed':good,'transforms_or_parents_changed':transformed,'non_target_changes':other,
            'uv_metrics':metrics,'atlas':atlas,'textures':textures,'triangulated':triangulated,'target_count':len(names),
            'texture_projection':[(t['image'],t['projection']) for t in mapping['texture_chains']]}
    (OUT/(label+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':good,'transform_changes':len(transformed),'non_target_changes':len(other),'atlas':atlas,'triangulated':triangulated}))


if __name__=='__main__':
    label=sys.argv[sys.argv.index('--')+1]
    if label=='snapshot':
        (OUT/'source_fingerprint.json').write_text(json.dumps(snapshot(),ensure_ascii=False),encoding='utf-8')
        print('Saved source fingerprint')
    else: validate(label)
