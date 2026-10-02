"""Compile thin-linen refinement and restrained corridor aggregate flooring in native SD."""
from pathlib import Path
import sys,subprocess,json,hashlib
sys.path.insert(0,str(Path(__file__).parent))
# Reuse the existing native graph builder definitions without rerunning its published export loop.
src=(Path(__file__).parent/'architecture_build_sd.py').read_text(encoding='utf8').split('rows=[]')[0]
src=src.replace('outlow=.31,outhigh=.19','outlow=.57,outhigh=.42').replace('(.78,.74,.64,1)','(.88,.85,.77,1)')
exec(compile(src,'architecture_build_sd.py','exec'))
M=R/'02_assets/materials/architecture_corridor';T=R/'02_assets/textures/generated/architecture_corridor_sd'
M.mkdir(parents=True,exist_ok=True);T.mkdir(parents=True,exist_ok=True)

def floor_graph():
    """Return a fine mineral aggregate waxed floor with shallow directional service scuffs."""
    g=Graph();fine=g.inst('Fine mineral aggregate','noise_bnw_spots_2',0,0,params={'scale':('Int1',120),'randomseed':('Int32',912)})
    chips=g.levels('Small aggregate inclusions',fine,250,0,.55,.76,.12,.70)
    bc=g.blend('Warm grey mineral binder',g.uniform('Binder',(.28,.29,.26,1),300,-240),g.uniform('Pale aggregate',(.42,.43,.39,1),300,-100),650,-160,chips)
    scratch=g.inst('Sparse service scuffs','grunge_scratches_fine',0,330,params={'balance':('Float1',.3),'contrast':('Float1',.5),'scratches_amount':('Float1',.06)})
    rr=g.levels('Wax variation at fine aggregate',fine,400,300,outlow=.30,outhigh=.42)
    rr=g.blend('Shallow scuffs in wax',rr,g.uniform('Scuff roughness',.57,400,500),800,300,scratch,opacity=.11)
    ht=g.levels('Level polished relief',chips,800,100,outlow=.485,outhigh=.515)
    normal=g.inst('Physical polished aggregate relief','height_to_normal_world_units',1080,100,{'input':ht},{'surface_size':('Float1',50),'height_depth':('Float1',.008),'normal_format':('Int1',1)},graph='height_to_normal_world_units_2')
    for i,(name,h,use) in enumerate([('BaseColor',bc,'baseColor'),('Roughness',rr,'roughness'),('Height',ht,'height'),('Normal',normal,'normal'),('Metallic',g.uniform('Dielectric',0,900,650),'metallic')]):g.output(name,h,1450,i*220,use)
    return g,{},.5,.00008

rows=[]
for name in ['thin_linen','corridor_floor']:
    g,entries,tile,depth=build('linen') if name=='thin_linen' else floor_graph()
    source=save(g,name);dest=T/name;dest.mkdir(exist_ok=True);commands=[]
    commands.append([str(SD/'sbscooker.exe'),'--inputs',str(source),'--output-path',str(M),'--alias','sbs://'+str(SD/'resources/packages')])
    commands.append([str(SD/'sbsrender.exe'),'render','--inputs',str(source.with_suffix('.sbsar')),'--output-path',str(dest),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report'])
    for k,p in entries.items():commands[-1]+=['--set-entry',k+'@'+str(p)]
    for i,cmd in enumerate(commands):
        with (C/f'corridor_{name}_{i}.log').open('w',encoding='utf8') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    files=[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(Image.open(p).size),'bit_depth':p.read_bytes()[24],'colorspace':'sRGB' if p.stem=='BaseColor' else 'Non-Color'} for p in dest.glob('*.png')]
    rows.append({'name':name,'source':source.relative_to(R).as_posix(),'commands':commands,'tile_metres':tile,'height_range_metres':depth,'inputs':{k:str(p) for k,p in entries.items()},'files':files})
    print('CORRIDOR_SD_READY',name,flush=True)
(T/'manifest.json').write_text(json.dumps({'date':'2026-09-12','materials':rows,'license':'Linen input ambientCG Fabric030 CC0; floor native Substance nodes'},indent=2),encoding='utf8')
