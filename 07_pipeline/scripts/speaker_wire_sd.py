"""制作编织喇叭网罩的 SD 金属微表面；编织起伏由真实圆线几何承担。"""
import json
import build_shell_tin_sd as sd

sd.M=sd.R/'02_assets/materials/speaker_wire'
sd.T=sd.R/'02_assets/textures/generated/speaker_wire'
sd.C=sd.R/'07_pipeline/cache/speaker_wire'
for p in (sd.M,sd.T,sd.C):p.mkdir(parents=True,exist_ok=True)
g=sd.graph('speaker_wire')
g.g.find('./attributes/description').set('v','Drawn steel wire microfinish. Woven geometry is authored separately with actual openings. Visual reference: Vasyl Kysylychak / XJlmWw. No third-party files embedded.')
tint=g.expose('WireColor','Steel wire color',(.47,.49,.48,1),'Surface',typ='Float4')
aging=g.expose('AgeAmount','Dull oxide variation',.27,'Surface',0,1)
cloud=g.inst('Restrained oxidation','noise_clouds_2',0,0,params={'scale':('Int1',4),'randomseed':('Int32',432)})
fine=g.inst('Fine drawn wire finish','noise_anisotropic_noise',0,350,params={'X_Amount':('Int1',8),'Y_Amount':('Int1',256),'smoothness':('Float1',.75)})
base=g.uniform('Neutral steel',(.47,.49,.48,1),350,-250,tint)
base=g.blend('Very subtle dulling',base,g.uniform('Oxide tone',(.30,.32,.31,1),350,0),750,-250,cloud,opacity=aging)
rough=g.levels('Polished to dull metal',cloud,500,350,outlow=.27,outhigh=.43)
rough=g.blend('Wire drawing sheen',rough,g.levels('Fine roughness',fine,500,650,outlow=.28,outhigh=.41),850,350,opacity=.2)
height=g.levels('Submicron metal relief',fine,1000,650,outlow=.48,outhigh=.52)
record=sd.finish(g,'speaker_wire',base,rough,height,g.uniform('Metal conductivity',1,1400,400),11,tilecm=10,depthcm=.0008)
record.update(date='2026-09-16',reference='https://www.artstation.com/artwork/XJlmWw',author='Vasyl Kysylychak',reference_use='Visual reference only; original graph; no downloaded third-party assets',normal='OpenGL',seed=3087,geometry='Actual over-under woven round wires; no opaque texture-filled holes')
(sd.T/'manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
