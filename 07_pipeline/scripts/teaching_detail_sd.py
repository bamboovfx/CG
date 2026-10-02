"""Compile/export genuine SD material refinements from original print and placement masks.
Editable native graphs own material synthesis; Pillow inputs are only declared graphics/placement.
"""
from pathlib import Path
import teaching_build_sd as b
R=b.R;D=R/'02_assets/materials/teaching_rebuild/detail_inputs'
b.M=R/'02_assets/materials/teaching_rebuild/detail';b.M.mkdir(exist_ok=True)
b.T=R/'02_assets/textures/generated/teaching_sd/detail';b.T.mkdir(exist_ok=True);b.rows=[]

def basegrain(g,scale=200):
    """Input graph and micro grain scale; return fiber, stain and scratch signals."""
    fiber=g.inst('Fine surface tooth','noise_perlin_noise',0,300,params={'scale':('Int1',scale)})
    stain=g.inst('Uneven age and handling','noise_clouds_2',0,550,params={'scale':('Int1',5)})
    scratch=g.inst('Fine use scratches','grunge_scratches_fine',0,800,params={'balance':('Float1',.44),'contrast':('Float1',.64),'scratches_amount':('Float1',.35)})
    return fiber,stain,scratch

def board():
    """SD turns authored eraser trajectories into pigment residue, powder film and differentiated roughness."""
    g=b.graph('teaching_detail_chalkboard');photo=b.input_image(g,'LicensedEraserPhoto');finger=b.input_image(g,'Handling',False)
    trajectory=g.filt('Extract mineral density from CC0 reference photograph','grayscaleconversion',0,-250,{'input1':photo},channels=2)
    fiber,stain,scratch=basegrain(g,320)
    residue=g.blend('Chalk embedded in erased paths',trajectory,stain,650,0,mode=3,opacity=.12)
    residue=g.levels('Recover chalk bundle variation',residue,850,0,.12,.84)
    pigment=g.uniform('Dense green board paint',(.032,.113,.072,1),650,-240)
    bc=g.blend('Grey green mineral chalk remnants',pigment,g.uniform('Mineral residue',(.37,.41,.31,1),850,-240),1100,0,residue,opacity=.32)
    bc=g.blend('Handling visible only at grazing light',bc,g.uniform('Oily touch darkening',(.018,.054,.036,1),800,210),1300,0,finger,opacity=.12)
    rough=g.blend('Powder roughness',g.uniform('Board paint roughness',.53,600,450),g.uniform('Powder film roughness',.86,900,450),1100,450,residue)
    rough=g.blend('Polished handling ridges',rough,g.uniform('Handling roughness',.35,850,720),1400,450,finger,opacity=.6)
    h=g.blend('Pigment tooth beneath powder',g.levels('Paint microheight',fiber,650,950,outlow=.48,outhigh=.53),g.levels('Thin deposited chalk film',residue,950,950,outlow=.48,outhigh=.75),1300,950,opacity=.2)
    b.finish(g,'teaching_detail_chalkboard',bc,rough,h,4.14,.00020,extras=[('ResidueMask',residue,None)],entry={'LicensedEraserPhoto':D/'chalkboard-blackboard-with-eraser-marks.jpg','Handling':D/'handling_ridges.png'},size=12)

def eraser():
    """Native woven cotton surface: visible thread reflectance and chalk loaded high-roughness fibers."""
    g=b.graph('teaching_detail_eraser');weave=g.inst('Woven cotton threads','weave_1',0,0,params={'Tiling':('Int1',90)})
    cloud=g.inst('Powder trapped in nap','noise_clouds_2',0,280,params={'scale':('Int1',7)})
    bc=g.blend('Woven dark textile reflectance',g.uniform('Dyed textile',(.055,.070,.062,1),350,-250),g.uniform('Thread catchlight',(.12,.15,.13,1),550,-250),800,0,weave,opacity=.6)
    bc=g.blend('Embedded mineral powder',bc,g.uniform('Chalk loaded nap',(.30,.31,.24,1),800,250),1100,0,cloud,opacity=.32)
    rr=g.levels('Diffuse woven fiber',weave,1100,420,outlow=.77,outhigh=.96)
    b.finish(g,'teaching_detail_eraser',bc,rr,weave,.15,.00045)

def books():
    """One editable SD graph yields fifteen individually weathered cover/spine material sets."""
    g=b.graph('teaching_detail_book');cover=b.input_image(g,'CoverArtwork');spine=b.input_image(g,'SpineArtwork');wear=b.input_image(g,'WearPlacement',False);finger=b.input_image(g,'Handling',False)
    fiber,stain,scratch=basegrain(g,260)
    weave=g.inst('Bookcloth loose woven fibers','fibers_1',100,1100,params={'Tiling':('Int1',22)})
    w=g.blend('Abraded threads at real cover boundary',wear,scratch,500,0,opacity=.06)
    raw=g.uniform('Exposed worn textile fibers',(.50,.44,.30,1),700,-300)
    def aged(art,y):
        """Input cover or spine artwork; return print softened by scuffing, dirt and cloth breakup."""
        out=g.blend('Faded edge cloth',art,raw,900,y,w,opacity=.75)
        out=g.blend('Uneven hand soil',out,g.uniform('Book finger soil',(.11,.095,.073,1),1100,y+170),1300,y,stain,opacity=.12)
        return g.blend('Faint handling ridge tint',out,g.uniform('Oil stained pigment',(.08,.072,.055,1),1300,y+220),1550,y,finger,opacity=.07)
    bc=aged(cover,0);sp=aged(spine,600)
    rough=g.blend('Scuffed cloth surface',g.uniform('Coated cloth roughness',.64,650,1350),g.uniform('Frayed fibers roughness',.88,1000,1350),1300,1250,w)
    rough=g.blend('Palm sheen',rough,g.uniform('Pressed cloth sheen',.39,900,1600),1500,1250,finger,opacity=.45)
    h=g.blend('Woven microscopic thread relief',weave,fiber,1050,1850,opacity=.23)
    presets=[(f'book_{i:02}',{'CoverArtwork':D/f'book_{i:02}_cover.png','SpineArtwork':D/f'book_{i:02}_spine.png','WearPlacement':D/f'book_{i:02}_wear.png','Handling':D/'handling_ridges.png'},{}) for i in range(15)]
    b.finish(g,'teaching_detail_book',bc,rough,h,.35,.00018,extras=[('SpineColor',sp,None)],presets=presets)

def notices():
    """Printed classroom graphics on lightly yellowed cellulose, localized dirty edges and paper wrinkles."""
    g=b.graph('teaching_detail_notice');art=b.input_image(g,'OriginalPrint');fiber,stain,scratch=basegrain(g,290)
    shape=g.inst('Paper clean interior','shape',0,1100,params={'Size':('Float1',.92),'Pattern':('Int1',1)})
    edge=g.levels('Paper edge oxidation',shape,330,1100,outlow=1,outhigh=0)
    bc=g.blend('Age uneven paper stock',art,g.uniform('Paper foxing tint',(.49,.39,.24,1),600,-300),850,0,stain,opacity=.055)
    bc=g.blend('Handled and oxidized paper edge',bc,g.uniform('Warm worn paper boundary',(.44,.35,.24,1),900,-260),1180,0,edge,opacity=.17)
    rough=g.levels('Fibers scatter light',fiber,1050,440,outlow=.73,outhigh=.86)
    h=g.blend('Fibrous tooth with soft storage wrinkles',fiber,stain,1050,780,opacity=.12)
    b.finish(g,'teaching_detail_notice',bc,rough,h,.3,.00008,presets=[(f'notice_{i:02}',{'OriginalPrint':D/f'notice_{i:02}_art.png'},{}) for i in range(6)])

def wood():
    """Original SD wood is further weathered with contact polish, shallow crossing scratches and ground-in dirt."""
    g=b.graph('teaching_detail_wood');base=b.input_image(g,'PreviousWoodColor');normal=b.input_image(g,'PreviousWoodNormal');finger=b.input_image(g,'Handling',False)
    fiber,stain,scratch=basegrain(g,350)
    scratches=g.levels('Shallow cut distribution',scratch,400,600,.46,.79)
    bc=g.blend('Dark cuts through old finish',base,g.uniform('Ground in scratch soil',(.12,.075,.032,1),500,-240),850,0,scratches,opacity=.20)
    bc=g.blend('Repeated hand contact dirt',bc,g.uniform('Dark touch soil',(.10,.07,.037,1),900,-240),1170,0,finger,opacity=.16)
    rr=g.levels('Worn varnish variation',stain,700,400,outlow=.27,outhigh=.51)
    rr=g.blend('Cuts expose rough wood',rr,g.uniform('Bare wood cut roughness',.73,900,650),1200,400,scratches,opacity=.5)
    rr=g.blend('Handled varnish polished smooth',rr,g.uniform('Hand polish sheen',.18,1100,700),1450,400,finger,opacity=.75)
    hh=g.levels('Cut into varnish film',scratch,1000,1000,outlow=.48,outhigh=.51)
    old=R/'02_assets/textures/generated/teaching_sd/teaching_varnished_wood'
    b.finish(g,'teaching_detail_wood',bc,rr,hh,.5,.00020,normal_in=normal,entry={'PreviousWoodColor':old/'BaseColor.png','PreviousWoodNormal':old/'Normal.png','Handling':D/'handling_ridges.png'},size=12)

if __name__=='__main__':
    board();books();notices();wood();eraser()
