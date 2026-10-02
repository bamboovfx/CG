"""新增稀疏表面脏渍：原生4K位置蒙版＋SD扫描细碎内容，独立于旧化与磨损。

输入：板材物理尺度、CC0扫描颜色／粗糙度；输出：两份原生SBS/SBSAR与脏渍通道。
参考照片仅观察，不采样；蒙版按毫米尺度直接采样，不修改已有工艺／表现图。
"""
from pathlib import Path
import json
import subprocess
import uuid
import xml.etree.ElementTree as E
import numpy as np
from build_desk_substance import Graph
from tripo_wood_detail_sd import bitmap,colour_levels,save,SCAN,SD
from wood_layers_sd import annotate

ROOT=Path(__file__).resolve().parents[2]
TEX=ROOT/'02_assets/textures/generated/tripo_wood_dirt'
MAT=ROOT/'02_assets/materials/tripo_wood_dirt'
WORK=ROOT/'07_pipeline/cache/tripo_wood_dirt_20260930'
SIZE=4096


def mark(canvas,x,y,rx,ry,strength,rng,soft=False):
    """输入技术蒙版、UV中心／半径／强度和随机源；叠加边界破碎的局部污斑。"""
    # 仅采样局部包围框；连续亚像素采样避免细点退化成随机单像素。
    radius=max(rx,ry)*2.7
    xa=max(0,int((x-radius)*SIZE)); xb=min(SIZE,int((x+radius)*SIZE)+1)
    ya=max(0,int((1-y-radius)*SIZE)); yb=min(SIZE,int((1-y+radius)*SIZE)+1)
    if xb<=xa or yb<=ya: return
    u=((np.arange(xa,xb,dtype=np.float32)+.5)/SIZE-x)[None,:]
    v=(1-(np.arange(ya,yb,dtype=np.float32)+.5)/SIZE-y)[:,None]
    angle=float(rng.uniform(0,np.pi)); c=np.cos(angle); s=np.sin(angle)
    a=(u*c-v*s)/rx; b=(u*s+v*c)/ry
    theta=np.arctan2(b,a); radial=np.sqrt(a*a+b*b)
    phases=rng.uniform(0,6.28,3)
    boundary=1+.18*np.sin(theta*3+phases[0])+.11*np.sin(theta*7+phases[1])+.055*np.sin(theta*13+phases[2])
    q=radial/np.maximum(boundary,.3)
    profile=np.exp(-q*q*1.45) if soft else np.clip((1.06-q)*5,0,1)
    # 每个斑点都有主体／浅边／断续内部，避免等大的实心黑圆。
    variation=.66+.22*np.sin(a*9+phases[0])*np.sin(b*8+phases[1])+.12*np.cos(a*21+b*13)
    value=profile*variation*strength
    np.maximum(canvas[ya:yb,xa:xb],value,out=canvas[ya:yb,xa:xb])


def placement(board):
    """输入板类别，返回细点、附着残留、淡擦抹三种直接4K采样位置图。"""
    folder=TEX/board/'placement'; folder.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(93157+(board=='back'))
    width,height=(.371,.38) if board=='seat' else (.361,.190)
    maps={name:np.zeros((SIZE,SIZE),np.float32) for name in ['Specks','Residue','Smudges']}
    centres=[(.20,.81),(.77,.70),(.55,.43),(.11,.36),(.69,.18)] if board=='seat' else [(.12,.54),(.73,.34),(.60,.89)]
    for k in range(165 if board=='seat' else 72):
        if k%3:
            cx,cy=centres[k%len(centres)]; x,y=rng.normal(cx,.045),rng.normal(cy,.045)
        else: x,y=rng.uniform(.04,.96,2)
        radius=rng.uniform(.00012,.00040)
        mark(maps['Specks'],x,y,radius/width,radius*rng.uniform(.60,1.25)/height,rng.uniform(.28,.85),rng)
    for k in range(39 if board=='seat' else 17):
        cx,cy=centres[k%len(centres)]; x,y=rng.normal(cx,.055),rng.normal(cy,.055)
        radius=rng.uniform(.00030,.00115)
        mark(maps['Residue'],x,y,radius/width,radius*rng.uniform(.55,1.4)/height,rng.uniform(.35,.82),rng)
    # 少量有辨识度的1.5–3mm残留，仍限定小面积，不覆盖宽幅木纹。
    anchors=[(.225,.79),(.68,.72),(.81,.41),(.11,.35),(.59,.46),(.30,.61)] if board=='seat' else [(.16,.55),(.73,.31),(.60,.85)]
    for x,y in anchors:
        mark(maps['Residue'],x,y,.0013/width,.00085/height,.91,rng)
        mark(maps['Specks'],x-.001,y+.001,.0003/width,.00038/height,.8,rng)
    smudges=[(.19,.82,.009,.0038),(.75,.72,.008,.004),(.58,.44,.011,.004),(.10,.36,.007,.005),(.69,.18,.008,.003)] if board=='seat' else [(.13,.54,.007,.004),(.73,.32,.009,.003)]
    for x,y,rx,ry in smudges:
        mark(maps['Smudges'],x,y,rx/width,ry/height,.24,rng,True)
    for name,field in maps.items(): save(field,folder/(name+'.png'))
    return folder


def build(board):
    """输入木板类型，编译不影响已有层的表面脏渍通道；输出记录与原生配方。"""
    folder=placement(board); dest=TEX/board; g=Graph(); identifier='wood_surface_dirt_'+board
    for element in (g.p,g.g): element.find('identifier').set('v',identifier)
    g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,identifier+'20260930'))+'}')
    g.g.find('./attributes/label').set('v','Surface dirt / '+board)
    g.g.find('./attributes/description').set('v','Independent surface residue, tiny clustered dark specks and faint wipe smudges. Direct 4096 placement; CC0 scan colour and roughness supply broken contours/content. White mask deposits dirt. Height 0–25 micrometres, metallic 0. Existing process and ageing remain external unchanged.')
    strength=g.expose('Dirt','Dirt',1,'Surface dirt')
    place={name:bitmap(g,folder/(name+'.png')) for name in ['Specks','Residue','Smudges']}
    matrix=(.674,0,0,.692) if board=='seat' else (.656,0,0,.345)
    offset=(-.09,.08) if board=='seat' else (.13,-.11)
    scan={}
    for name,filename,colour in [('Color','wood_table_worn_diff_8k.jpg',True),('Rough','wood_table_worn_rough_8k.jpg',False)]:
        image=bitmap(g,SCAN/filename,colour,13)
        scan[name]=g.filt('实际物理尺度／'+name,'transformation',0,0,{'input1':image},{'matrix22':('Float4',matrix),'offset':('Float2',offset)},channels=1 if colour else 2)
    rough_detail=g.inst('实物微细变化','highpass',0,0,{'Source':scan['Rough']},{'Radius':('Float1',12)},graph='highpass_grayscale')
    modulation=g.levels('残留内部浓淡变化',rough_detail,0,0,.40,.60,.38,1)
    specks=g.filt('细点破边','warp',0,0,{'input1':place['Specks'],'inputgradient':rough_detail},{'intensity':('Float1',.000035)},channels=2)
    residue=g.filt('附着物不规则边界','warp',0,0,{'input1':place['Residue'],'inputgradient':rough_detail},{'intensity':('Float1',.00010)},channels=2)
    residue=g.blend('残留真实浓淡',residue,modulation,0,0,mode=3)
    smudge=g.blend('淡擦抹碎化',place['Smudges'],modulation,0,0,mode=3)
    mask=g.blend('细点与残留最大值',specks,residue,0,0,mode=5)
    mask=g.blend('局部擦抹并入',mask,smudge,0,0,mode=5)
    zero=g.uniform('归零',0,0,0); mask=g.blend('表面脏渍独立强度',zero,mask,0,0,opacity=strength)
    # 使用实物RGB结构，三类脏渍具有不同目标色；不用单一黑色盖住木纹。
    dark=colour_levels(g,scan['Color'],'深色细点',(.035,.018,.006),(.48,.26,.12),(.105,.073,.047),(.30,.22,.135))
    grey=colour_levels(g,scan['Color'],'灰褐残留',(.035,.018,.006),(.48,.26,.12),(.27,.245,.19),(.48,.425,.33))
    smear=colour_levels(g,scan['Color'],'淡褐擦抹',(.035,.018,.006),(.48,.26,.12),(.29,.19,.09),(.54,.35,.18))
    col=g.blend('灰褐残留颜色',smear,grey,0,0,place['Residue'])
    col=g.blend('最深处细点',col,dark,0,0,g.levels('细点着色范围',specks,0,0,0,.35))
    r=g.levels('干燥脏渍微变化',scan['Rough'],0,0,.15,.90,.60,.86)
    # 淡染色近乎无厚度；附着残留最多25µm，细点约6µm。
    h=g.blend('细点厚度比例',zero,specks,0,0,opacity=.24)
    h=g.blend('少量附着物厚度',h,residue,0,0,mode=5)
    h=g.blend('高度也能归零',zero,h,0,0,opacity=strength)
    outputs={'DirtMask':mask,'DirtColor':col,'DirtRoughness':r,'DirtHeight':h,'ResidueMask':residue,'SmudgeMask':smudge}
    for name,signal in outputs.items(): g.output(name,signal,0,0)
    annotate(g); path=MAT/(identifier+'.sbs'); E.indent(g.p); E.ElementTree(g.p).write(path,encoding='utf-8',xml_declaration=True)
    for k,command in enumerate([[str(SD/'sbscooker.exe'),'--inputs',str(path),'--output-path',str(MAT),'--alias','sbs://'+str(SD/'resources/packages')],
        [str(SD/'sbsrender.exe'),'render','--inputs',str(path.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']]):
        done=subprocess.run(command,capture_output=True,text=True)
        (WORK/f'{board}_sd_{k}.log').write_text(done.stdout+done.stderr,encoding='utf-8')
        if done.returncode: raise RuntimeError((done.stdout+done.stderr)[-2200:])
    print('SURFACE_DIRT_SD '+board,flush=True)
    return {'board':board,'source':str(path.relative_to(ROOT)),'outputs':list(outputs),'surface_m':(.371,.38) if board=='seat' else (.361,.190)}


def main():
    """生成独立表面层和来源清单；已有工艺／表现文件不写入。"""
    for folder in (TEX,MAT,WORK): folder.mkdir(parents=True,exist_ok=True)
    boards=[build(board) for board in ['seat','back']]
    (TEX/'manifest.json').write_text(json.dumps({'boards':boards,'resolution':4096,'height_distance_m':.000025,
        'scan_manifest':'02_assets/textures/external/polyhaven_wood_detail/manifest.json','reference':'User supplied close-ups, observation only','generated_placement':'Direct 4096 analytic sampling, no resampling of reference pixels'},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__': main()
