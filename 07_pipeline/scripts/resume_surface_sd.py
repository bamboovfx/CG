"""Author native SD micro surfaces at explicit closeup scale, separate from broad artwork.

Outputs: editable SBS/SBSAR and 4K linear height/roughness/normal maps.
No product photograph is baked into these physical surface channels.
"""
import teaching_build_sd as b
b.M=b.R/'02_assets/materials/closeup_surface';b.M.mkdir(parents=True,exist_ok=True)
b.T=b.R/'02_assets/textures/generated/closeup_surface';b.T.mkdir(parents=True,exist_ok=True)
b.C=b.R/'07_pipeline/cache/detail_resume';b.rows=[]

def build(kind,tile,depth,rough):
    """Input physical family/scale/depth/roughness; export multiscale SD surface channels."""
    g=b.graph('closeup_'+kind)
    fine=g.inst('Submillimetre surface grains','noise_perlin_noise',0,0,params={'scale':('Int1',220)})
    cloud=g.inst('Local polishing and age','noise_clouds_2',0,250,params={'scale':('Int1',5)})
    scratch=g.inst('Broken contact scratches','grunge_scratches_fine',0,500,params={'balance':('Float1',.46),'contrast':('Float1',.8),'scratches_amount':('Float1',.23)})
    cuts=g.levels('Sparse individual fine cuts',scratch,360,500,.60,.87)
    if kind=='cloth':
        weave=g.inst('Warp and weft threads','weave_1',0,780,params={'Tiling':('Int1',72)})
        height=g.blend('Woven thread relief with fibre tooth',weave,fine,680,0,opacity=.12)
    elif kind=='paper':
        fibres=g.inst('Loose cellulose fibres','fibers_1',0,780,params={'Tiling':('Int1',38)})
        height=g.blend('Cellulose tooth and embedded fibres',fine,fibres,680,0,opacity=.4)
    else:
        height=g.levels('Fine substrate height',fine,400,0,outlow=.47,outhigh=.55)
        height=g.blend('Cuts remove a thin surface film',height,g.levels('Negative scratch relief',cuts,400,780,outlow=.54,outhigh=.03),680,0,opacity=.55)
    rr=g.levels('Small polished and matte variations',cloud,850,320,outlow=max(.1,rough-.15),outhigh=min(.95,rough+.12))
    rr=g.blend('Scratch grooves scatter grazing light',rr,g.uniform('Dry groove response',.77,900,630),1150,320,cuts,opacity=.8)
    bc=g.levels('Restrained substrate reflectance detail',fine,1100,0,outlow=.82,outhigh=.96)
    b.finish(g,'closeup_'+kind,bc,rr,height,tile,depth,extras=[('ScratchMask',cuts,None)],size=12)

if __name__=='__main__':
    for spec in [('varnish',.22,.00016,.36),('polymer',.18,.000065,.46),('paper',.10,.00006,.8),('cloth',.12,.00018,.74),('chalk',.18,.000045,.66)]:
        build(*spec)
