"""以原生8K扫描细节重做旧木材表现，位置蒙版和表面内容分离。

输入：CC0木桌Diffuse/Rough/Displacement、已认可工艺图、Tripo轮廓。
输出：原生SD配方、真实4K处理图、细节色图和五通道；不改原工艺文件。
手工定向蒙版直接在4096采样，参考照片只用于观察，不采样像素。
"""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image
from build_desk_substance import Graph,put
from wood_layers_sd import annotate

ROOT=Path(__file__).resolve().parents[2]
MAT=ROOT/'02_assets/materials/tripo_wood_detail'
TEX=ROOT/'02_assets/textures/generated/tripo_wood_detail'
OLD=ROOT/'02_assets/textures/generated/tripo_wood_reference'
WORK=ROOT/'07_pipeline/cache/tripo_wood_detail_20260930'
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
SCAN=ROOT/'02_assets/textures/external/polyhaven_wood_detail/wood_table_worn'
PARAMS={'Scratches':.85,'Age':.70,'Wear':.80}
SIZE=4096


def save(array,path):
    """输入0–1技术蒙版和路径，保存原生4K的16位标量图。"""
    Image.fromarray((np.clip(array,0,1)*65535).astype(np.uint16)).save(path)


def placement(board,hull):
    """输入板类型与真实轮廓，生成位置包络、稀疏磕碰和有切削结构的划痕。"""
    out=TEX/board/'placement'; out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(93081+(board=='back'))
    u=np.linspace(0,1,SIZE,dtype=np.float32)[None,:]
    v=np.linspace(1,0,SIZE,dtype=np.float32)[:,None]
    edge=np.ones((SIZE,SIZE),np.float32)
    for a,b in zip(hull,hull[1:]+hull[:1]):
        dx=b[0]-a[0]; dy=b[1]-a[1]
        distance=(dx*(v-a[1])-dy*(u-a[0]))/max((dx*dx+dy*dy)**.5,1e-8)
        np.minimum(edge,distance,out=edge)
    age=np.full_like(edge,.21); contact=np.zeros_like(edge); flakes=np.zeros_like(edge)
    patches=[(.22,.73,.20,.18,.72),(.71,.42,.24,.24,.52),(.51,.90,.31,.11,.44)] if board=='seat' else [(.20,.50,.18,.30,.64),(.72,.78,.28,.25,.58)]
    for x,y,sx,sy,strength in patches:
        age+=strength*np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.6)
    use=[(.24,.85,.13,.055,.44),(.77,.80,.12,.07,.36),(.30,.65,.065,.05,.24)] if board=='seat' else [(.08,.55,.055,.26,.33),(.74,.90,.15,.045,.30)]
    for x,y,sx,sy,strength in use:
        contact+=strength*np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.8)
    # 边缘只留毫米级间断磕碰，不再做数厘米宽的浅色装饰带。
    edge_band=np.clip(1-edge/.008,0,1)
    for _ in range(44 if board=='seat' else 26):
        x,y=float(rng.uniform(.02,.98)),float(rng.uniform(.02,.98))
        axis=int(rng.integers(0,4))
        if axis==0: x=.007
        elif axis==1: x=.993
        elif axis==2: y=.993
        else: y=.007
        sx=float(rng.uniform(.0025,.012)); sy=float(rng.uniform(.0025,.009))
        flakes=np.maximum(flakes,np.exp(-(((u-x)/sx)**2+((v-y)/sy)**2)*1.3)*float(rng.uniform(.6,1)))
    chips=flakes*edge_band
    contact=np.maximum(contact,edge_band*.24)
    core=np.zeros_like(edge); lip=np.zeros_like(edge)
    lines=[(.14,.46,.31,.18,.00065),(.21,.44,.37,.25,.00045),(.64,.53,.79,.28,.00060),
        (.69,.60,.84,.37,.00038),(.40,.69,.55,.53,.00042),(.52,.64,.60,.42,.00033),
        (.08,.27,.21,.17,.00045),(.59,.25,.77,.22,.00035),(.38,.37,.51,.48,.0003),(.79,.65,.90,.52,.0004)]
    if board=='back': lines=[(.24,.65,.45,.64,.00045),(.69,.31,.81,.41,.00035)]
    for index,(x0,y0,x1,y1,width) in enumerate(lines):
        dx=x1-x0; dy=y1-y0; denom=dx*dx+dy*dy
        t=np.clip(((u-x0)*dx+(v-y0)*dy)/denom,0,1)
        taper=.12+.88*np.maximum(np.sin(np.pi*t),0)**.7
        # 核心沟槽与单侧掀起纤维分开；划痕不是均匀白线。
        wiggle=.0007*np.sin(t*7+index)+.00015*np.sin(t*61+index*2)
        dist=(dx*(v-y0-dy*t-wiggle)-dy*(u-x0-dx*t))/denom**.5
        ends=np.clip(t*200,0,1)*np.clip((1-t)*200,0,1)
        w=width*taper*(.84+.16*np.sin(t*49+index))
        track=np.exp(-(dist/np.maximum(w,1e-6))**2)*ends
        fibre_lip=np.exp(-((dist-w*1.8)/np.maximum(w*.72,1e-6))**2)*ends*(.28+.22*np.sin(t*26+index)**2)
        np.maximum(core,track*(.85 if index%3 else .55),out=core)
        np.maximum(lip,fibre_lip,out=lip)
    # 原细划痕保留低对比，只当微擦痕，不再统一加深。
    fine=np.asarray(Image.open(OLD/board/'ScratchDark.png'),dtype=np.float32)/65535
    core=np.maximum(core,fine*.17)
    maps={'AgePlacement':age,'ContactPlacement':contact,'EdgeChips':chips,'ScratchCore':core,'ScratchLip':lip}
    for name,array in maps.items(): save(array,out/(name+'.png'))
    return out


def bitmap(g,path,colour=False,power=12):
    """输入实际资源、色彩模式和原始分辨率，创建不降采样的包内位图。"""
    did=g.uid(); d=put(g.deps,'dependency')
    for k,v in [('filename','?himself'),('uid',did),('type','package'),('fileUID',0),('versionUID',0)]: put(d,k,v)
    r=put(g.p.find('content'),'resource'); name=path.stem
    for k,v in [('identifier',name),('uid',g.uid()),('type','bitmap'),('format',path.suffix[1:]),('colorSpace','[use_embedded_profile]' if colour else '[linear]'),('filepath',path.as_posix())]: put(r,k,v)
    h=g.filt('来源／'+name,'bitmap',0,0,params={'bitmapresourcepath':('String',f'pkg:///{name}?dependency={did}'),'colorswitch':('Bool',int(colour))},channels=1 if colour else 2)
    p=g.nodes[-1].find('./compImplementation/compFilter/parameters/parameter')
    p.find('relativeTo').set('v','0'); p.find('./paramValue/constantValueInt2').set('v',f'{power} {power}')
    return h


def colour_levels(g,source,label,low,high,outlow,outhigh):
    """输入RGB影像和逐通道范围，保留真实扫描色彩差异而不是常量着色。"""
    params={k:('Float4',tuple(v)+(a,)) for k,v,a in [('levelinlow',low,0),('levelinhigh',high,1),('leveloutlow',outlow,0),('levelouthigh',outhigh,1)]}
    return g.filt(label,'levels',0,0,{'input1':source},params,channels=1)


def build(board,hull):
    """输入木板与轮廓，以扫描实物相关细节编译独立表现和最终PBR通道。"""
    folder=placement(board,hull); out=TEX/board; g=Graph(); identifier='wood_detail_'+board
    for element in (g.p,g.g): element.find('identifier').set('v',identifier)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,identifier+'20260930'))+'}')
    g.g.find('./attributes/label').set('v','Scanned finish ageing / '+board)
    g.g.find('./attributes/description').set('v','Approved process maps preserved. Original Poly Haven wood_table_worn CC0 8192px colour/roughness/displacement supply correlated fine detail. Asset-directed 4096px placement is separate. Surface width 37.1/36.1 cm. No reference photo pixels. Final normal OpenGL.')
    controls={k:g.expose(k,k,v,'表现层强度') for k,v in PARAMS.items()}
    # 8K源覆盖约55cm；裁切到木板实际37cm宽，处理后输出4K。
    matrix=(.674,0,0,.692) if board=='seat' else (.656,0,0,.345)
    offset=(-.09,.08) if board=='seat' else (.13,-.11)
    scan={}
    for name,filename,colour in [('Color','wood_table_worn_diff_8k.jpg',True),('Rough','wood_table_worn_rough_8k.jpg',False),('Height','wood_table_worn_disp_8k.png',False)]:
        signal=bitmap(g,SCAN/filename,colour,13)
        scan[name]=g.filt('实际尺寸裁切／'+name,'transformation',0,0,{'input1':signal},{'matrix22':('Float4',matrix),'offset':('Float2',offset)},channels=1 if colour else 2)
    place={name:bitmap(g,folder/(name+'.png')) for name in ['AgePlacement','ContactPlacement','EdgeChips','ScratchCore','ScratchLip']}
    luma=g.filt('扫描／只用于污点识别','grayscaleconversion',0,0,{'input1':scan['Color']},channels=2)
    colour_detail=g.inst('真实污痕高频','highpass',0,0,{'Source':luma},{'Radius':('Float1',18)},graph='highpass_grayscale')
    dark_pores=g.levels('实际凹点与嵌色',colour_detail,0,0,.43,.49,1,0)
    rough_var=g.levels('实际涂层擦亮与雾化',scan['Rough'],0,0,.25,.82,.30,1)
    age_mask=g.blend('老化位置乘扫描变化',place['AgePlacement'],rough_var,0,0,mode=3)
    dirt_mask=g.blend('局部凹点保留细碎颜色',dark_pores,place['AgePlacement'],0,0,mode=3,opacity=1)
    # 真实纹理只控制破损细节，不用拉长随机噪声模拟木纤维。
    worn=g.levels('扫描涂层破损区',scan['Rough'],0,0,.42,.72,.08,1)
    contact=g.blend('接触包络乘实物破损',place['ContactPlacement'],worn,0,0,mode=3)
    wear=g.blend('细小边缘磕碰叠加',contact,place['EdgeChips'],0,0,mode=5)
    wear=g.filt('边界微磨蚀','warp',0,0,{'input1':wear,'inputgradient':colour_detail},{'intensity':('Float1',.00020)},channels=2)
    age_col=colour_levels(g,scan['Color'],'真实多色旧涂层',(0.035,.018,.006),(.48,.26,.12),(.31,.17,.058),(.76,.52,.25))
    wear_col=colour_levels(g,scan['Color'],'露木色：保留灰褐／赭色／浅纤维',(0.035,.018,.006),(.48,.26,.12),(.39,.29,.16),(.79,.67,.44))
    dirt_col=colour_levels(g,scan['Color'],'嵌色：深褐细点',(0.035,.018,.006),(.48,.26,.12),(.13,.060,.022),(.39,.23,.09))
    age_rough=g.levels('局部旧漆粗糙度',scan['Rough'],0,0,.15,.90,.34,.63)
    wear_rough=g.levels('真实裸露纤维粗糙度',scan['Rough'],0,0,.15,.90,.53,.78)
    hp=g.inst('从扫描高度分离浅表起伏','highpass',0,0,{'Source':scan['Height']},{'Radius':('Float1',14)},graph='highpass_grayscale')
    age_h=g.levels('旧漆微起伏',hp,0,0,.455,.545,.43,.57)
    wear_h=g.levels('露木浅凹和细孔',hp,0,0,.455,.545,.15,.43)
    # 划痕沟槽和掀起纤维独立，轻微变形与实物细纹共用。
    core=g.filt('沟槽沿实物纤维细碎变化','warp',0,0,{'input1':place['ScratchCore'],'inputgradient':colour_detail},{'intensity':('Float1',.00008)},channels=2)
    lip=g.blend('毛边受真实孔隙打断',place['ScratchLip'],g.levels('毛边变化',rough_var,0,0,outlow=.35,outhigh=1),0,0,mode=3)
    raw={'AgeMask':age_mask,'AgeColor':age_col,'AgeRoughness':age_rough,'AgeHeight':age_h,'DirtMask':dirt_mask,'DirtColor':dirt_col,
         'WearMask':wear,'WearColor':wear_col,'WearRoughness':wear_rough,'WearHeight':wear_h,'ScratchCore':core,'ScratchLip':lip}
    proc={name:bitmap(g,OLD/board/('Process_'+name+'.png'),name in ('BaseColor','Normal')) for name in ['BaseColor','Roughness','Normal','Metallic','AO','Height']}
    # Normal是RGB数据，修正其资源颜色空间，避免把切线向量当作sRGB色彩。
    for r in g.p.findall('./content/resource'):
        if r.find('identifier').get('v')=='Process_Normal': r.find('colorSpace').set('v','[linear]')
    zero=g.uniform('零',0,0,0); half=g.uniform('中性高度',.5,0,0)
    def scale(label,source,control):
        """输入标量信号与公开强度，返回保持归零的效果权重。"""
        return g.blend(label,zero,source,0,0,opacity=control)
    am=scale('老化强度',age_mask,controls['Age']); dm=scale('凹点嵌色强度',dirt_mask,controls['Age'])
    wm=scale('磨损强度',wear,controls['Wear']); sm=scale('沟槽强度',core,controls['Scratches']); lm=scale('毛边强度',lip,controls['Scratches'])
    c=g.blend('旧漆多色变化',proc['BaseColor'],age_col,0,0,am)
    c=g.blend('局部嵌色细点',c,dirt_col,0,0,dm,opacity=.42)
    c=g.blend('真实露木色',c,wear_col,0,0,wm)
    c=g.blend('沟槽深色与残漆',c,dirt_col,0,0,sm,opacity=.77)
    c=g.blend('划伤单侧浅纤维',c,wear_col,0,0,lm)
    rough=g.blend('旧漆真实反射',proc['Roughness'],age_rough,0,0,am)
    rough=g.blend('露木反射',rough,wear_rough,0,0,wm)
    rough=g.blend('划痕反射',rough,wear_rough,0,0,sm)
    # 高度以1mm完整范围编码：已认可木孔21.6µm、局部浅损伤分开求和。
    # 以中性0.5编码有正负的高度，避免Blend默认钳位吞掉负凹槽。
    effect_height=g.blend('旧化细起伏／120µm比例',half,age_h,0,0,am,opacity=.12)
    effect_height=g.blend('露木凹陷／220µm比例',effect_height,wear_h,0,0,wm,opacity=.22)
    effect_height=g.blend('100µm划痕沟槽',effect_height,g.uniform('沟槽高度0.4',.4,0,0),0,0,sm)
    effect_height=g.blend('30µm局部纤维掀起',effect_height,g.uniform('毛边高度0.53',.53,0,0),0,0,lm)
    effect_n=g.inst('表现层毫米尺度OpenGL法线','height_to_normal_world_units',0,0,{'input':effect_height},{'surface_size':('Float1',37.1 if board=='seat' else 36.1),'height_depth':('Float1',.10),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    normal=g.inst('切线法线叠加','normal_combine',0,0,{'Input':proc['Normal'],'Input_1':effect_n},{'blend_quality':('Int1',1)})
    final={'BaseColor':c,'Roughness':rough,'Normal':normal,'Metallic':proc['Metallic'],'AO':proc['AO'],'EffectHeight':effect_height}
    for name,signal in raw.items(): g.output('Raw_'+name,signal,0,0)
    for name,signal in final.items(): g.output(name,signal,0,0,{'BaseColor':'baseColor','Roughness':'roughness','Normal':'normal','Metallic':'metallic','AO':'ambientOcclusion'}.get(name))
    annotate(g); path=MAT/(identifier+'.sbs'); E.indent(g.p); E.ElementTree(g.p).write(path,encoding='utf-8',xml_declaration=True)
    for k,command in enumerate([[str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')],
        [str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(out),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]):
        done=subprocess.run(command,capture_output=True,text=True); (WORK/f'{board}_sd_{k}.log').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-2500:])
    print('DETAIL_SD_DONE '+board,flush=True)
    return {'board':board,'source':str(path.relative_to(ROOT)),'raw_outputs':list(raw),'final_outputs':list(final),'crop_matrix':matrix,'crop_offset':offset}


def main():
    """保护工艺源，生成两套扫描辅助材质和实际来源清单。"""
    for folder in (TEX,MAT,WORK): folder.mkdir(parents=True,exist_ok=True)
    inspection=json.loads((ROOT/'07_pipeline/cache/tripo_wood_appearance_20260930/input_inspection.json').read_text(encoding='utf-8'))
    protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OLD.glob('*/Process_*.png')}
    boards=[build(board,inspection['boards'][obj]['uv_hull']) for board,obj in [('seat','LP_part_02'),('back','LP_part_09')]]
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    (TEX/'manifest.json').write_text(json.dumps({'boards':boards,'parameters':PARAMS,'placement_resolution':SIZE,'source_resolution':8192,
        'output_resolution':4096,'protected_process_files':protected,'source_manifest':'02_assets/textures/external/polyhaven_wood_detail/manifest.json',
        'height_distance_m':{'Age':.00012,'Wear':.00022,'Scratches':.00010,'ScratchLip':.00003}},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__': main()
