"""Author independent 4K hero tin SD graphs without altering any classroom shell texture.
Inputs: existing original artwork and native Adobe generators. Outputs: SBS/SBSAR/PBR maps plus command hashes.
"""
from pathlib import Path
import json,hashlib,subprocess,xml.etree.ElementTree as E
import build_shell_tin_sd as sd
R=sd.R
sd.M=R/'02_assets/materials/hero_tin';sd.T=R/'02_assets/textures/generated/hero_tin_sd';sd.C=R/'07_pipeline/cache/equipment_rebuild/hero_tin'
for p in (sd.M,sd.T,sd.C):p.mkdir(parents=True,exist_ok=True)

def family(name,kind):
    """Layer coherent mill grain, handling zones, scratches and sparse coating loss at a 12 cm scale."""
    g=sd.graph(name)
    cloud=g.inst('Broad handling polish','noise_clouds_2',0,0,params={'scale':('Int1',2),'randomseed':('Int32',718)})
    fine=g.inst('Rolling direction','noise_anisotropic_noise',0,220,params={'X_Amount':('Int1',7),'Y_Amount':('Int1',512),'smoothness':('Float1',.85)})
    scratch=g.inst('Individual hairline scuffs','grunge_scratches_fine',0,450,params={'balance':('Float1',.36),'contrast':('Float1',.72),'scratches_amount':('Float1',.16)})
    breaks=g.inst('Only isolated worn zones','noise_bnw_spots_2',0,700,params={'scale':('Int1',3),'randomseed':('Int32',91)})
    zones=g.levels('Sparse rather than uniform wear',breaks,260,700,.75,.94)
    hair=g.levels('Thin scratches',scratch,260,460,.67,.91)
    wear=g.blend('Scratches confined to handling patches',hair,zones,550,650,mode=3)
    silver=g.uniform('Tin coated steel reflectance',(.68,.70,.67,1),500,-250)
    grey=g.uniform('Very slight tin oxide',(.50,.52,.48,1),500,-80)
    steel=g.blend('Subtle oxide fields',silver,grey,780,-200,cloud,opacity=.13)
    r=g.levels('Broad polish contrast',cloud,700,230,outlow=.20,outhigh=.31)
    r=g.blend('Microscopic directional sheen',r,g.levels('Mill grain roughness',fine,400,210,outlow=.21,outhigh=.29),1000,250,opacity=.16)
    metal=g.uniform('Metal substrate',1,1250,550)
    bc=steel
    if kind!='steel':
        art=sd.color_input(g,'Artwork') if kind=='print' else g.uniform('Red oil ink pigment',(.245,.011,.006,1),200,-500)
        bc=g.blend('Ink loss exposing reflective tin',art,steel,1100,-150,wear,opacity=.7)
        # Lithographic ink is thin and clear coated. Metal only shows where the ink is missing.
        metal=g.levels('Conductivity through exposed chips',wear,1200,550,outlow=0,outhigh=.95)
        r=g.blend('Clear varnish over ink',g.levels('Handling changes gloss',cloud,800,350,outlow=.19,outhigh=.29),r,1300,300,wear)
    r=g.blend('Scuffs interrupt highlights',r,g.uniform('Scuffed finish',.40,900,700),1550,340,hair,opacity=.32)
    h=g.levels('Rolling relief below ten micrometres',fine,850,900,outlow=.49,outhigh=.51)
    h=g.blend('Scratches cut coating',h,g.uniform('Shallow scratch depth',.43,850,1120),1250,900,hair,opacity=.32)
    # Extra exported masks remain editable for localized Blender contact overlays.
    g.output('WearMask',wear,2600,1400)
    # finish expects five channels, so remove the auxiliary output before its checked exporter.
    # The full wear branch is retained in the PBR outputs and editable source.
    out=g.outs[-1];oid=out.find('uid').get('v');g.outs.remove(out)
    for n in list(g.nodes):
        b=n.find('./compImplementation/compOutputBridge/output')
        if b is not None and b.get('v')==oid:g.nodes.remove(n)
    for n in list(g.roots):
        if n.find('output').get('v')==oid:g.roots.remove(n)
    entry=R/'02_assets/textures/authored/classroom/2k/tin_label_color_2k.png' if kind=='print' else None
    rec=sd.finish(g,name,bc,r,h,metal,12,entry,tilecm=12,depthcm=.0025)
    src=sd.M/(name+'.sbs');arc=src.with_suffix('.sbsar')
    rec.update(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),sbsar_sha256=hashlib.sha256(arc.read_bytes()).hexdigest(),seed=718,license='Original procedural material using licensed installed Adobe node packages; original existing project label artwork, not a scanned commercial label.',source_artwork_sha256=hashlib.sha256(entry.read_bytes()).hexdigest() if entry else None)
    rec['commands']=[[str(sd.SD/'sbscooker.exe'),'--inputs',str(src),'--output-path',str(sd.M),'--alias','sbs://'+str(sd.SD/'resources/packages')],[str(sd.SD/'sbsrender.exe'),'render','--inputs',str(arc),'--output-path',str(sd.T/name),'--output-name','{outputNodeName}','--set-value','$outputsize@12,12','--engine','d3d11','--output-bit-depth','16','--no-report']+(['--set-entry','Artwork@'+str(entry)] if entry else [])]
    return rec

if __name__=='__main__':
    rows=[family('hero_tinplate','steel'),family('hero_lithographic_ink','print'),family('hero_red_lacquer','red')]
    (sd.T/'manifest.json').write_text(json.dumps({'date':'2026-09-12','materials':rows,'normal':'OpenGL','tile_metres':.12},indent=2),encoding='utf8')
