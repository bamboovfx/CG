"""制作木椅原生SD分层材质；输入既有CC0木纹，输出工艺通道、效果蒙版和参数清单。

工艺层：木纤维／着色／打磨涂层。表现层：划痕／老化／磨损，分别控制。
只写本轮的新材质目录；不修改已有木材配方或教室镜头。
"""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import xml.etree.ElementTree as E

from PIL import Image
import numpy as np
from build_desk_substance import Graph, put

ROOT = Path(__file__).resolve().parents[2]
SD = Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
SOURCE = ROOT / '02_assets/textures/polyhaven/plywood/4k/plywood_diff_4k.jpg'
MAT = ROOT / '02_assets/materials/wood_layers'
TEX = ROOT / '02_assets/textures/generated/wood_layers'
WORK = ROOT / '07_pipeline/cache/wood_layers_20260930'


def color_input(g):
    """输入Graph实例，创建包内CC0位图资源并返回连接句柄；打开源文件即可预览。"""
    dependency_id=g.uid()
    dependency=put(g.deps,'dependency'); put(dependency,'filename','?himself')
    put(dependency,'uid',dependency_id); put(dependency,'type','package')
    put(dependency,'fileUID',0); put(dependency,'versionUID',0)
    resource=put(g.p.find('content'),'resource')
    put(resource,'identifier','PlywoodColor_CC0'); put(resource,'uid',g.uid())
    put(resource,'type','bitmap'); put(resource,'format','jpg')
    put(resource,'colorSpace','[use_embedded_profile]'); put(resource,'filepath',SOURCE.as_posix())
    handle=g.filt('工艺层／CC0自然木纤维','bitmap',0,0,params={'bitmapresourcepath':('String',f'pkg:///PlywoodColor_CC0?dependency={dependency_id}'),'colorswitch':('Bool',1)},channels=1)
    # 位图资源明确保留4K，避免归档采用较低的默认资源分辨率。
    parameter=g.nodes[-1].find('./compImplementation/compFilter/parameters/parameter')
    parameter.find('relativeTo').set('v','0'); parameter.find('./paramValue/constantValueInt2').set('v','12 12')
    return handle


def annotate(g):
    """输入完整Graph，按连接深度排布节点并创建独立中文说明；保留原生节点默认名称。"""
    depths, columns = {}, {}
    for index, node in enumerate(g.nodes):
        upstream = [int(c.find('connRef').get('v')) for c in node.findall('./connections/connection')]
        depth = max((depths.get(uid, 0) + 1 for uid in upstream), default=0)
        depths[int(node.find('uid').get('v'))] = depth
        row = columns.get(depth, 0); columns[depth] = row + 1
        x, y = depth * 370, row * 310
        node.find('./GUILayout/gpos').set('v', f'{x} {y} 0')
        if index < len(g.labels):
            item = put(g.gui, 'GUIObject'); put(item, 'type', 'COMMENT')
            layout = put(item, 'GUILayout')
            put(layout, 'gpos', f'{x-25} {y-70} -100'); put(layout, 'size', '290 45')
            put(item, 'GUIName', ''); put(item, 'uid', g.uid())
            put(item, 'title', g.labels[index][0]); put(item, 'isTitleVisible', 1)
            put(item, 'isFrameVisible', 1)


def main():
    """读取已验证节点库，构造分层配方并烹制渲染；输出哈希、参数与通道统计。"""
    for folder in (MAT, TEX, WORK): folder.mkdir(parents=True, exist_ok=True)
    assert SOURCE.is_file(), SOURCE
    g = Graph()
    for element in (g.p, g.g): element.find('identifier').set('v', 'school_wood_layers')
    g.p.find('fileUID').set('v', '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'school-wood-layers-20260930')) + '}')
    g.g.find('./attributes/label').set('v', 'School wood: process and appearance')
    g.g.find('./attributes/description').set('v', '0.6 m tile, OpenGL. Wood and clear finish metalness=0. CC0 scan is colour input, reference photograph is visual research only.')
    scratch_amount = g.expose('Scratches', '划痕强度', .38, '02 表现层', 0, 1)
    age_amount = g.expose('Age', '老化强度', .30, '02 表现层', 0, 1)
    wear_amount = g.expose('Wear', '磨损强度', .42, '02 表现层', 0, 1)
    finish_r = g.expose('FinishRoughness', '涂层基础粗糙度', .34, '01 工艺层', .15, .7)
    tile_cm = g.expose('SurfaceSize', '纹理覆盖宽度（cm）', 60, '03 物理尺度', 10, 150)
    depth = g.expose('HeightRange', '高度范围（cm）', .012, '03 物理尺度', .001, .05)

    # 工艺层：扫描只提供自然木纹颜色，程序纤维与涂层响应独立生成。
    scan = color_input(g)
    fibre = g.inst('工艺层／细木纤维', 'wood_fibers_2', 0, 0)
    cloud = g.inst('工艺层／生长曲线', 'noise_clouds_2', 0, 0, params={'scale': ('Int1', 2), 'randomseed': ('Int32', 441)})
    scan = g.filt('工艺层／按木板横向校正扫描纹理','transformation',0,0,{'input1':scan},{'matrix22':('Float4',(0,1,-1,0))},channels=1)
    scan = g.filt('工艺层／连续自然生长弧线','warp',0,0,{'input1':scan,'inputgradient':cloud},{'intensity':('Float1',.028)},channels=1)
    scan = g.blend('工艺层／带色透明涂层',scan,g.uniform('琥珀涂层滤色',(.94,.78,.5,1),0,0),0,0,mode=3)
    fibre = g.filt('工艺层／纤维轻微弯曲', 'warp', 0, 0, {'input1': fibre, 'inputgradient': cloud}, {'intensity': ('Float1', .003)})
    grain = g.levels('工艺层／纤维对比', fibre, 0, 0, .15, .85, .08, .92)
    amber = g.blend('工艺层／琥珀色着色', g.uniform('木纹暗色', (.32,.13,.018,1),0,0), g.uniform('木纹亮色', (.68,.32,.055,1),0,0), 0,0,grain)
    base = g.blend('工艺层／自然木纹与染色', amber, scan, 0,0,opacity=.58)
    # 灰度0／1混合将公开单值精确映射为基础粗糙度。
    r_base = g.blend('工艺层／基础粗糙度参数',g.uniform('粗糙度零点',0,0,0),g.uniform('粗糙度满值',1,0,0),0,0,opacity=finish_r)
    r_variation = g.levels('工艺层／微弱涂层变化',cloud,0,0,outlow=.25,outhigh=.45)
    rough = g.blend('工艺层／打磨涂层响应',r_base,r_variation,0,0,opacity=.12)
    height = g.levels('工艺层／涂层下木纹微起伏',grain,0,0,outlow=.485,outhigh=.515)
    zero = g.uniform('木材与清漆／Metallic 0',0,0,0)
    ao = g.uniform('平面木纹／AO 白色',1,0,0)

    # 表现层的空间蒙版独立输出，供资产级边缘和接触区域再约束。
    scratches = g.inst('表现层／细浅划痕','grunge_scratches_fine',0,0)
    scratch_source = scratches
    scratches = g.levels('表现层／稀疏划痕',scratches,0,0,.56,.74,0,1)
    long_scratches = g.inst('表现层／少量交叉使用划痕','pattern_scratches_generator',0,0,params={'spline_number':('Int1',20),'spline_scale':('Float1',.13),'spline_width':('Float1',1.1),'spline_width_in_pixel':('Bool',1),'spline_rotation_random':('Float1',.85),'spline_scale_random':('Float1',.65),'spline_distortion_random':('Float1',.15),'randomseed':('Int32',589)},graph='scratches_generator')
    scratches = g.blend('表现层／细浅与长划痕合并',scratches,long_scratches,0,0,mode=5)
    age = g.inst('表现层／不均匀老化','noise_clouds_2',0,0,params={'scale':('Int1',3),'randomseed':('Int32',903)})
    age = g.levels('表现层／老化分布',age,0,0,.70,.94,0,1)
    wear = g.inst('表现层／磨损破碎','noise_dirt_3',0,0,params={'scale':('Int1',4),'randomseed':('Int32',277)})
    wear = g.levels('表现层／露木斑块',wear,0,0,.08,.30,0,1)
    final_color = g.blend('老化／颜色轻微褪色',base,g.uniform('老化木色',(.48,.32,.16,1),0,0),0,0,age,opacity=age_amount)
    scratch_color_mask = g.levels('划痕／轻微颜色变化',scratches,0,0,outlow=0,outhigh=.14)
    final_color = g.blend('划痕／轻微露出浅色',final_color,g.uniform('划伤木色',(.62,.43,.22,1),0,0),0,0,scratch_color_mask,opacity=scratch_amount)
    long_color_mask = g.levels('长划痕／凹槽色差',long_scratches,0,0,outlow=0,outhigh=.6)
    final_color = g.blend('长划痕／暗色细沟',final_color,g.uniform('沟槽颜色',(.12,.05,.015,1),0,0),0,0,long_color_mask,opacity=scratch_amount)
    final_color = g.blend('磨损／露出木纤维',final_color,g.uniform('露木颜色',(.45,.29,.14,1),0,0),0,0,wear,opacity=wear_amount)
    final_rough = g.blend('老化／涂层劣化',rough,g.uniform('老化粗糙度',.52,0,0),0,0,age,opacity=age_amount)
    final_rough = g.blend('划痕／反射散射',final_rough,g.uniform('划痕粗糙度',.59,0,0),0,0,scratches,opacity=scratch_amount)
    final_rough = g.blend('磨损／干燥露木',final_rough,g.uniform('露木粗糙度',.65,0,0),0,0,wear,opacity=wear_amount)
    final_height = g.blend('划痕／浅沟槽',height,g.uniform('划痕深度',.38,0,0),0,0,scratches,opacity=scratch_amount)
    final_height = g.blend('磨损／细纤维起伏',final_height,g.levels('干燥纤维高度',grain,0,0,outlow=.46,outhigh=.54),0,0,wear,opacity=wear_amount)
    normals = []
    for label, h in [('工艺层／OpenGL微法线',height),('表现层／合成高度转法线',final_height)]:
        normals.append(g.inst(label,'height_to_normal_world_units',0,0,{'input':h},{'surface_size':tile_cm,'height_depth':depth,'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2'))
    outputs = [('Process_BaseColor',base,None),('Process_Roughness',rough,None),('Process_Metallic',zero,None),('Process_Normal',normals[0],None),('Process_AO',ao,None),('BaseColor',final_color,'baseColor'),('Roughness',final_rough,'roughness'),('Metallic',zero,'metallic'),('Normal',normals[1],'normal'),('AO',ao,'ambientOcclusion'),('Height',height,None),('Grain',grain,None),('ScratchSource',scratch_source,None),('ScratchMask',scratches,None),('LongScratchMask',long_scratches,None),('AgeMask',age,None),('WearBreakup',wear,None)]
    for name, handle, usage in outputs: g.output(name,handle,0,0,usage)
    annotate(g)
    src=MAT/'school_wood_layers.sbs'; E.indent(g.p); E.ElementTree(g.p).write(src,encoding='utf-8',xml_declaration=True)
    commands=[ [str(SD/'sbscooker.exe'),'--inputs',str(src),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')], [str(SD/'sbsrender.exe'),'render','--inputs',str(src.with_suffix('.sbsar')),'--output-path',str(TEX),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report'] ]
    for index, command in enumerate(commands):
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/f'sd_build_{index}.txt').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-4000:])
    files=[]
    for path in sorted(TEX.glob('*.png')):
        im=Image.open(path); arr=np.asarray(im); peak=np.iinfo(arr.dtype).max
        files.append({'path':str(path.relative_to(ROOT)),'size':list(im.size),'extrema':im.getextrema(),'mean_normalized':float(arr.mean()/peak),'coverage_above_0_1':float((arr>peak*.1).mean()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'colorspace':'sRGB' if 'BaseColor' in path.stem else 'Non-Color'})
    manifest={'source':str(src.relative_to(ROOT)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scan_source':'https://polyhaven.com/a/plywood','scan_license':'CC0','scan_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'tile_metres':.6,'height_range_m':.00012,'normal_format':'OpenGL','parameters':{'Scratches':.38,'Age':.30,'Wear':.42,'FinishRoughness':.34},'nodes':len(g.nodes),'commands':commands,'files':files,'note':'Generic SD wear is a tile demonstration. Blender restricts wear with asset-specific edge masks. AO remains white for shallow surface detail.'}
    (TEX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'native_source':str(src),'outputs':len(files),'nodes':len(g.nodes)},ensure_ascii=False))


if __name__ == '__main__':
    main()
