"""原生 Substance Designer 图负责涂层/磨损/粉笔分层，原创行为遮罩作为显式输入。"""
from pathlib import Path
import xml.etree.ElementTree as E
import hashlib,json,subprocess,uuid
from PIL import Image
from build_desk_substance import Graph,put
from teaching_build_sd import input_image

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
SD=Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
M=ROOT/'02_assets/materials/blackboard_age'
T=ROOT/'02_assets/textures/generated/blackboard_age'
C=ROOT/'07_pipeline/cache/blackboard_age_20260919'
T.mkdir(parents=True,exist_ok=True)
g=Graph()
for owner in [g.p,g.g]:owner.find('identifier').set('v','school_blackboard_baked_coating')
g.p.find('fileUID').set('v','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'blackboard_age_20260919'))+'}')
g.g.find('./attributes/label').set('v','School blackboard | baked coating and use history')
g.g.find('./attributes/description').set('v','Original spatial masks plus CC0 eraser-detail photograph, high-pass filtered as a chalk placement mask. Baked green coating, polished upper use zone, embedded chalk, felt sweeps, subtle window-side fading; lower quarter less used. Colour/roughness are authored independently, not scanned PBR. Surface 4.1438 x 1.49 m. Fine coating tooth is added at render time. Exposure mask is an artistic assumption, not a measured UV dose.')

def mask(name,x,y):
    """输入遮罩名及节点位置；返回默认灰度输入桥，原始节点标题保持默认。"""
    return g.image_input(name,x,y)

use=mask('UseMask',-1000,-550)
abrasion=mask('Abrasion',-1000,-300)
dust=mask('EmbeddedChalk',-1000,0)
wipe=mask('EraserPasses',-1000,300)
sun=mask('SunFade',-1000,600)
ghost=mask('GhostWriting',-1000,900)
edge=mask('EdgeDust',-1000,1200)
soil=mask('TouchSoil',-1000,1500)
fade_amount=g.expose('SunFadeAmount','Sun fade strength',.38,'Age',0,.8)
dust_amount=g.expose('EmbeddedChalkAmount','Embedded chalk',.11,'Use',0,.7)
wipe_amount=g.expose('RecentWipeAmount','Recent eraser traces',.10,'Use',0,.7)
polish_amount=g.expose('PolishAmount','Eraser polishing',.82,'Use',0,1)
ghost_amount=g.expose('GhostAmount','Old writing fragments',.08,'Use',0,1)
detail_amount=g.expose('ChalkDetailAmount','Fine chalk and felt striations',.38,'Use',0,.8)
photo=input_image(g,'CC0EraserDetail')
gray=g.filt('Extract only residue density','grayscaleconversion',-700,1900,{'input1':photo},channels=2)
hp=g.inst('Remove broad photographic illumination','highpass',-400,1900,{'Source':gray},{'Radius':('Float1',48)},graph='highpass_grayscale')
detail=g.levels('Positive fine chalk ridges',hp,0,1900,.46,.74)
detail=g.blend('Exclude little-used lower quarter',detail,use,400,1900,mode=3)

# 颜色层：保持墨绿底漆，变色与积灰分开；不将太阳光斑烘进 BaseColor。
clean=g.uniform('Dense green baked coating',(.125,.205,.167,1),-500,-550)
bc=g.blend('Slow broad window-side fading',clean,g.uniform('Desaturated aged pigment',(.230,.277,.218,1),-500,-300),-100,-500,sun,opacity=fade_amount)
bc=g.blend('Chalk lodged in coating tooth',bc,g.uniform('Old neutral mineral chalk',(.54,.57,.53,1),-100,-220),300,-500,dust,opacity=dust_amount)
bc=g.blend('Recently redistributed fine chalk',bc,g.uniform('Soft fresh chalk residue',(.48,.53,.49,1),300,-220),700,-500,wipe,opacity=wipe_amount)
bc=g.blend('Almost erased writing fragments',bc,g.uniform('Ghost strokes',(.62,.64,.58,1),700,-200),1100,-500,ghost,opacity=ghost_amount)
bc=g.blend('Sparse touch soil',bc,g.uniform('Darkened hand contact',(.105,.15,.12,1),1050,-200),1450,-500,soil,opacity=.22)
bc=g.blend('Dust trapped at lowest groove only',bc,g.uniform('Powder at tray seam',(.59,.59,.50,1),1420,-150),1770,-500,edge,opacity=.30)
bc=g.blend('Real felt fibres and granular chalk',bc,g.uniform('Neutral chalk residue',(.52,.55,.51,1),1780,-170),2080,-500,detail,opacity=detail_amount)

# 微齿先被磨平，然后上覆粉末；因此磨损和积灰对粗糙度的作用相反。
rr=g.blend('Abrasion flattens coating tooth',g.uniform('New coating roughness',.62,-400,200),g.uniform('Polished coating roughness',.29,-200,400),250,220,abrasion,opacity=polish_amount)
rr=g.blend('Embedded mineral film scatters light',rr,g.uniform('Powder roughness',.89,280,500),700,220,dust,opacity=.42)
rr=g.blend('Recent felt path roughness',rr,g.uniform('Fresh powder roughness',.82,720,500),1100,220,wipe,opacity=.24)
rr=g.blend('Faint handling sheen',rr,g.uniform('Contact polished surface',.31,1040,540),1450,220,soil,opacity=.45)
rr=g.blend('Groove powder',rr,g.uniform('Seam powder roughness',.94,1400,570),1770,220,edge,opacity=.5)
rr=g.blend('Granular residue breaks polished reflection',rr,g.uniform('Fine mineral roughness',.89,1750,600),2070,220,detail,opacity=.35)

# 原生微尺度输入用于薄粉层法线，实际烤漆颗粒在 Blender 用米制坐标叠加。
grain=g.uniform('Smooth coating base; fine tooth added in shader',.5,-350,1000)
h=g.levels('Very small coating relief',grain,150,1000,outlow=.48,outhigh=.52)
h=g.blend('Thin embedded chalk film',h,g.levels('Chalk film depth',dust,150,1250,outlow=.50,outhigh=.60),650,1000,opacity=.22)
norm=g.inst('Micrometre OpenGL normal','height_to_normal_world_units',1300,1000,{'input':h},
            {'surface_size':('Float1',414.3805),'height_depth':('Float1',.004),'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
outputs=[('BaseColor',bc,'baseColor'),('Roughness',rr,'roughness'),('Normal',norm,'normal'),('Height',h,'height'),
         ('Metallic',g.uniform('Paint is dielectric',0,1800,1450),'metallic')]
for index,(name,handle,usage) in enumerate(outputs):g.output(name,handle,2250,index*240,usage)

# 说明写在独立注释框，避免把原生节点名改成不可对应教程的自定义名称。
for title,x,y in g.labels:
    frame=put(g.gui,'GUIObject');put(frame,'type','COMMENT')
    layout=put(frame,'GUILayout');put(layout,'gpos',f'{x-60} {y-85} -100');put(layout,'size','240 45')
    put(frame,'GUIName','');put(frame,'uid',g.uid());put(frame,'title',title)
    put(frame,'frameColor','.16 .25 .20 .8');put(frame,'isTitleVisible',1);put(frame,'isFrameVisible',1)
E.indent(g.p)
source=M/'school_blackboard_baked_coating.sbs'
E.ElementTree(g.p).write(source,encoding='utf-8',xml_declaration=True)
cook=[str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')]
with (C/'substance_cook.log').open('w') as log:subprocess.run(cook,stdout=log,stderr=subprocess.STDOUT,check=True)
render=[str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(T),
        '--output-name','{outputNodeName}','--set-value','$outputsize@12,11','--engine','d3d11','--output-bit-depth','16','--no-report']
names=['UseMask','Abrasion','EmbeddedChalk','EraserPasses','SunFade','GhostWriting','EdgeDust','TouchSoil']
for name in names:render+=['--set-entry',name+'@'+str(M/'inputs'/(name+'.png'))]
photo_path=ROOT/'02_assets/materials/teaching_rebuild/detail_inputs/chalkboard-blackboard-with-eraser-marks.jpg'
render+=['--set-entry','CC0EraserDetail@'+str(photo_path)]
with (C/'substance_render.log').open('w') as log:subprocess.run(render,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color'} for p in sorted(T.glob('*.png'))]
assert len(files)==5 and all(f['size']==[4096,2048] for f in files)
(T/'manifest.json').write_text(json.dumps({'method':'Native Substance Designer synthesis from original procedural placement masks',
 'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'seed':190926,'surface_m':[4.143805,1.49],'outputs':files,'commands':[cook,render],
 'photo_detail_input':{'path':photo_path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(photo_path.read_bytes()).hexdigest(),
 'license':'CC0 / Public Domain, verified 2026-09-19','url':'https://www.goodfreephotos.com/other-photos/chalkboard-blackboard-with-eraser-marks.jpg.php',
 'processing':'grayscale -> high pass (broad lighting removal) -> residue mask -> original use distribution'},
 'not_measured_pbr':True,'manufacturer_reference_pixels_used':False},indent=2),encoding='utf-8')
print('BLACKBOARD_SUBSTANCE_READY',len(files),flush=True)
