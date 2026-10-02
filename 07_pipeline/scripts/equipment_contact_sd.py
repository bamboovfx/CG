"""Create genuine editable SD contact-film mask: oval touched zone, warped ridge traces and micro scratches."""
import json,hashlib
import build_shell_tin_sd as sd
R=sd.R;sd.M=R/'02_assets/materials/equipment_rebuild';sd.T=R/'02_assets/textures/generated/equipment_sd';sd.C=R/'07_pipeline/cache/equipment_rebuild'
g=sd.graph('equipment_contact_film')
oval=g.inst('Soft touch footprint','shape',0,0,params={'Pattern':('Int1',5),'Size_xy':('Float2',(.68,.90))})
cloud=g.inst('Nonuniform wiping pressure','noise_clouds_2',0,250,params={'scale':('Int1',3),'randomseed':('Int32',122)})
ridge=g.inst('Parallel wiping and skin ridge traces','noise_anisotropic_noise',0,520,params={'X_Amount':('Int1',4),'Y_Amount':('Int1',85),'smoothness':('Float1',.68)})
ridge=g.filt('Curved traces in residue','warp',300,520,{'input1':ridge,'inputgradient':cloud},{'intensity':('Float1',.025)})
mask=g.blend('Broken soft footprint',oval,cloud,600,0,mode=3)
mask=g.blend('Coherent wiping detail',mask,g.levels('Restrained traces',ridge,600,500,outlow=.5,outhigh=1),850,0,mode=3)
rough=g.levels('Touched region different sheen',mask,1100,300,outlow=.14,outhigh=.38)
bc=g.blend('Amber residue under clear finish',g.uniform('Transparent film tone',(.5,.4,.24,1),600,-400),g.uniform('Dull handling tone',(.6,.52,.38,1),600,-200),1100,-200,mask)
height=g.levels('Film is submicron',ridge,1100,650,outlow=.499,outhigh=.501)
# Height stores the placement mask as well, while normal relief stays under 0.1 micrometre.
rec=sd.finish(g,'equipment_contact_film',bc,rough,mask,g.uniform('Nonmetallic residue',0,1200,900),11,tilecm=8,depthcm=.00001)
src=sd.M/'equipment_contact_film.sbs';arc=src.with_suffix('.sbsar');rec.update(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),sbsar_sha256=hashlib.sha256(arc.read_bytes()).hexdigest(),license='Original native procedural graph using locally licensed Adobe nodes. No photographic inputs.',placement='Height output is also the contact mask; normal depth 0.1 micrometre. UV patches identify actual hand/contact areas.',seed=122)
rec['commands']=[[str(sd.SD/'sbscooker.exe'),'--inputs',str(src),'--output-path',str(sd.M),'--alias','sbs://'+str(sd.SD/'resources/packages')],[str(sd.SD/'sbsrender.exe'),'render','--inputs',str(arc),'--output-path',str(sd.T/'equipment_contact_film'),'--output-name','{outputNodeName}','--set-value','$outputsize@11,11','--engine','d3d11','--output-bit-depth','16','--no-report']]
(sd.T/'contact_manifest.json').write_text(json.dumps(rec,indent=2),encoding='utf8')
