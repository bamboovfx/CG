"""Build the desk's editable native Substance graph; no bitmap source textures.

Inputs: Adobe's installed node library. Outputs: SBS source in assets/materials.
Public controls separate coating loss, oxidation, physical scale and microdetail.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import uuid

ROOT = Path(__file__).resolve().parents[2]
LIB = Path('D:/Program Files/Adobe/Adobe Substance 3D Designer/resources/packages')
DEST = ROOT / '02_assets/materials/school_desk'
DEST.mkdir(parents=True, exist_ok=True)


def put(parent, tag, value=None):
    """Append an XML field; return the element for subsequent child fields."""
    return E.SubElement(parent, tag, {} if value is None else {'v': str(value)})


def val(value):
    """Serialize a scalar/vector constant to Substance's space-separated format."""
    return ' '.join(map(str, value)) if isinstance(value, (tuple, list)) else str(value)


class Graph:
    """Small XML authoring layer for native nodes, connections and public controls."""

    def __init__(self):
        """Initialize a standalone package; IDs are deterministic within this build."""
        self.i = 1000
        self.p = E.Element('package')
        for k, v in [('identifier', 'school_desk_painted_steel'), ('formatVersion', '1.1.0.202502'),
                     ('updaterVersion', '1.1.0.202502'), ('fileUID', '{'+str(uuid.uuid5(uuid.NAMESPACE_URL, 'desk-painted-steel'))+'}'), ('versionUID', '0')]:
            put(self.p, k, v)
        self.deps = put(self.p, 'dependencies')
        self.depmap = {}
        self.g = put(put(self.p, 'content'), 'graph')
        put(self.g, 'identifier', 'desk_painted_steel')
        put(self.g, 'uid', self.uid())
        put(self.g, 'graphtype', 'material')
        a = put(self.g, 'attributes')
        put(a, 'label', 'School desk | aged enamel over steel')
        put(a, 'description', 'Native procedural enamel / exposed steel / layered rust. Reference: props_01; method inspiration Andrea Riccardi. Tile = 20 cm; height range = 0.06 cm. OpenGL normal. Wear and Age are independent. Optional placement mask is additive, white = remove paint. Curvature should be pre-masked to selected exposed edges. No baked illumination in base color.')
        self.outs = put(self.g, 'graphOutputs')
        self.inputs = put(self.g, 'paraminputs')
        self.nodes = put(self.g, 'compNodes')
        bp = put(self.g, 'baseParameters')
        self.param(bp, 'outputsize', ('Int2', (0, 0)))
        bp.find('./parameter/relativeTo').set('v', '1')
        self.param(bp, 'format', ('Int32', 1))
        self.param(bp, 'randomseed', ('Int32', 3087))
        self.gui = put(self.g, 'GUIObjects')
        opts = put(self.g, 'options')
        opt = put(opts, 'option'); put(opt, 'name', 'defaultParentSize'); put(opt, 'value', '12x12')
        self.roots = put(put(self.g, 'root'), 'rootOutputs')
        self.labels = []

    def uid(self):
        """Return the next package-local unique ID."""
        self.i += 1
        return self.i

    def param(self, parent, name, spec):
        """Write a typed constant or exposed-parameter getter to a node parameter."""
        typ, value = spec
        q = put(parent, 'parameter'); put(q, 'name', name); put(q, 'relativeTo', 0)
        pv = put(q, 'paramValue')
        if typ.startswith('@'):
            dtype = typ[1:]
            dv = put(pv, 'dynamicValue'); nid = self.uid(); put(dv, 'rootnode', nid)
            pn = put(put(dv, 'paramNodes'), 'paramNode'); put(pn, 'uid', nid)
            fn = 'get_integer1' if dtype == 'Int1' else 'get_' + dtype.lower()
            put(pn, 'function', fn); put(pn, 'type', {'Float1':256, 'Float4':2048, 'Int1':16}[dtype])
            fd = put(put(pn, 'funcDatas'), 'funcData'); put(fd, 'name', fn)
            put(put(fd, 'constantValue'), 'constantValueString', value)
        else:
            put(pv, 'constantValue'+typ, val(value))

    def expose(self, name, label, default, group, lo=0, hi=1, typ='Float1', desc=''):
        """Declare a user-facing parameter and return its typed getter specification."""
        p = put(self.inputs, 'paraminput'); put(p, 'identifier', name); put(p, 'uid', self.uid())
        a = put(p, 'attributes'); put(a, 'label', label); put(a, 'description', desc)
        put(p, 'type', {'Float1':256, 'Float4':2048, 'Int1':16}[typ])
        put(put(p, 'defaultValue'), 'constantValue'+typ, val(default))
        w = put(p, 'defaultWidget'); put(w, 'name', 'color' if typ=='Float4' else 'slider')
        opts = put(w, 'options')
        for k, v in [('min',lo),('max',hi),('clamp',1),('step',1 if typ=='Int1' else .01)]:
            opt = put(opts, 'option'); put(opt,'name',k); put(opt,'value',v)
        put(p, 'group', group)
        return ('@'+typ, name)

    def node(self, label, x, y, channels, connections):
        """Create a labeled node shell and wire its observed input identifiers."""
        n = put(self.nodes, 'compNode'); nid, oid = self.uid(), self.uid(); put(n,'uid',nid)
        cs = put(n, 'connections')
        for name, source in connections.items():
            c = put(cs, 'connection'); put(c,'identifier',name); put(c,'connRef',source[0]); put(c,'connRefOutput',source[1])
        put(put(n, 'GUILayout'), 'gpos', f'{x} {y} 0')
        co = put(put(n, 'compOutputs'), 'compOutput'); put(co,'uid',oid); put(co,'comptype',channels)
        self.labels.append((label, x, y))
        return n, (nid, oid, channels)

    def filt(self, label, kind, x, y, inputs=None, params=None, channels=2):
        """Add an atomic filter with explicit parameters; return its output handle."""
        n, h = self.node(label,x,y,channels,inputs or {})
        f = put(put(n,'compImplementation'),'compFilter'); put(f,'filter',kind)
        pp = put(f, 'parameters')
        self.param(pp,'outputsize',('Int2',(0,0)))
        pp.find('./parameter/relativeTo').set('v','1')
        for k,v in (params or {}).items(): self.param(pp,k,v)
        return h

    def inst(self, label, file, x, y, inputs=None, params=None, graph=None):
        """Instantiate an installed native library graph using its actual interface."""
        doc = E.parse(LIB/(file+'.sbs'))
        gs = doc.findall('./content/graph')
        sg = next((g for g in gs if g.find('identifier').get('v')==graph), gs[0])
        gid = sg.find('identifier').get('v')
        if file not in self.depmap:
            did = self.uid(); self.depmap[file] = did
            d = put(self.deps,'dependency'); put(d,'filename','sbs://'+file+'.sbs'); put(d,'uid',did)
            put(d,'type','package'); put(d,'fileUID',0); put(d,'versionUID',0)
        out = sg.find('./graphOutputs/graphoutput')
        channels = 2 if out.find('channels') is not None and out.find('channels').get('v')=='2' else 1
        n,h = self.node(label,x,y,channels,inputs or {})
        ci = put(put(n,'compImplementation'),'compInstance')
        put(ci,'path',f'pkg:///{gid}?dependency={self.depmap[file]}')
        pp = put(ci,'parameters')
        self.param(pp,'outputsize',('Int2',(0,0)))
        pp.find('./parameter/relativeTo').set('v','1')
        for k,v in (params or {}).items(): self.param(pp,k,v)
        b = put(put(ci,'outputBridgings'),'outputBridging'); put(b,'uid',h[1]); put(b,'identifier',out.find('identifier').get('v'))
        return h

    def uniform(self, label, color, x, y, exposed=None):
        """Create a grayscale or RGB material value; return its node output."""
        color_mode = isinstance(color,(list,tuple))
        spec = exposed or ('Float4',color if color_mode else (color,color,color,1))
        return self.filt(label,'uniform',x,y,params={'outputcolor':spec,'colorswitch':('Bool',int(color_mode))},channels=1 if color_mode else 2)

    def blend(self,label,bg,fg,x,y,mask=None,mode=0,opacity=1):
        """Combine material signals; foreground uses optional opacity mask."""
        inputs = {'destination':bg,'source':fg}
        if mask: inputs['opacity'] = mask
        return self.filt(label,'blend',x,y,inputs,{'blendingmode':('Int32',mode),'opacitymult':opacity if isinstance(opacity,tuple) else ('Float1',opacity)},channels=bg[2])

    def levels(self,label,source,x,y,low=0,high=1,outlow=0,outhigh=1):
        """Remap a grayscale field, preserving a consistent alpha range."""
        params = {k:('Float4',(v,v,v,a)) for k,v,a in [('levelinlow',low,0),('levelinhigh',high,1),('leveloutlow',outlow,0),('levelouthigh',outhigh,1)]}
        return self.filt(label,'levels',x,y,{'input1':source},params)

    def image_input(self, name, x, y):
        """Create optional black-default placement input; return the bridge output."""
        pid = self.uid(); p = put(self.inputs,'paraminput'); put(p,'identifier',name); put(p,'uid',pid)
        a = put(p,'attributes'); put(a,'label','Extra wear / edge placement'); put(a,'description','Optional: white removes coating. Supply a painted mask or selected curvature; default black leaves procedural distribution unchanged.')
        put(p,'isConnectable',1); put(p,'type',2); put(put(p,'defaultValue'),'constantValueFloat1',0)
        widget = put(p,'defaultWidget'); put(widget,'name',''); put(widget,'options')
        n,h = self.node('OPTIONAL ASSET WEAR MASK',x,y,2,{})
        b = put(put(n,'compImplementation'),'compInputBridge'); put(b,'entry',pid); put(b,'parameters')
        return h

    def output(self, name, source, x, y, usage=None):
        """Register an exported output with the correct PBR usage metadata."""
        oid = self.uid(); o = put(self.outs,'graphoutput'); put(o,'identifier',name); put(o,'uid',oid)
        put(put(o,'attributes'),'label',name)
        if usage:
            u = put(put(o,'usages'),'usage'); put(u,'components','RGBA'); put(u,'name',usage)
        if source[2]==2: put(o,'channels',2)
        put(o,'group','Material' if usage else 'Masks')
        n = put(self.nodes,'compNode'); put(n,'uid',self.uid())
        c = put(put(n,'connections'),'connection'); put(c,'identifier','inputNodeOutput'); put(c,'connRef',source[0]); put(c,'connRefOutput',source[1])
        put(put(n,'GUILayout'),'gpos',f'{x} {y} 0')
        put(put(put(n,'compImplementation'),'compOutputBridge'),'output',oid)
        r = put(self.roots,'rootOutput'); put(r,'output',oid); put(r,'format',0); put(r,'usertag','')

    def save(self):
        """Annotate each processing stage and serialize the native editable source."""
        for title,x,y in self.labels:
            q = put(self.gui,'GUIObject'); put(q,'type','COMMENT')
            gl = put(q,'GUILayout'); put(gl,'gpos',f'{x-65} {y-90} -100'); put(gl,'size','185 52')
            put(q,'GUIName',''); put(q,'uid',self.uid()); put(q,'title',title)
            put(q,'frameColor','0.19 0.25 0.27 0.8'); put(q,'isTitleVisible',1); put(q,'isFrameVisible',1)
        E.indent(self.p)
        path = DEST/'school_desk_painted_steel.sbs'
        E.ElementTree(self.p).write(path,encoding='utf-8',xml_declaration=True)
        print(f'{path}: {len(self.nodes)} native nodes, {len(self.inputs)} public inputs')


def build():
    """Assemble native procedural coating, oxidation and microgeometry branches."""
    g = Graph()
    wear = g.expose('Wear','Coating loss',.36,'01 Weathering',desc='Raises exposed-area coverage independently of oxidation age.')
    age = g.expose('Age','Oxidation age',.60,'01 Weathering',desc='Oxidation within exposed metal; intact enamel remains dielectric.')
    tint = g.expose('PaintColor','Grey ivory enamel',(.61,.61,.54,1),'02 Surface',typ='Float4')
    rust_tint = g.expose('RustColor','Oxide midtone',(.25,.115,.046,1),'02 Surface',typ='Float4')
    paint_r = g.expose('PaintRoughness','Paint roughness',.47,'02 Surface',.1,.85)
    dirt_amount = g.expose('DirtAmount','Embedded dirt',.14,'01 Weathering',0,.5)
    scale = g.expose('ChipScale','Chip distribution scale',3,'01 Weathering',1,12,'Int1')
    tile_cm = g.expose('SurfaceSize','Tile width (cm)',20,'03 Physical scale',2,100)
    depth = g.expose('HeightRange','Height range (cm)',.06,'03 Physical scale',.001,.2)
    # Multi-frequency removal field: clusters first, then small torn edges.
    spots = g.inst('01 CHIP CLUSTERS','noise_bnw_spots_2',0,0,params={'scale':scale})
    spots = g.inst('01b CONNECTED PAINT FLAKES','blur_hq',240,-280,{'Source':spots},{'Intensity':('Float1',.70),'Quality':('Int1',1)},graph='blur_hq_grayscale')
    cloud = g.inst('02 MACRO WEATHER','noise_clouds_2',0,220,params={'scale':('Int1',2),'randomseed':('Int32',51)})
    grain = g.inst('03 FRACTURED EDGE','noise_dirt_3',0,440,params={'scale':('Int1',4),'randomseed':('Int32',117)})
    # A tiny edge warp avoids turning coherent flakes into white metal pepper.
    warp = g.filt('04 IRREGULAR CONTOURS','warp',260,0,{'input1':spots,'inputgradient':grain},{'intensity':('Float1',.00018)})
    field = g.blend('05 CLUSTER VARIATION',warp,cloud,490,0,opacity=.20)
    chip = g.inst('06 COATING LOSS / WEAR','histogram_scan',720,0,{'Input_1':field},{'Position':wear,'Contrast':('Float1',.985)})
    extra = g.image_input('ExtraWear',490,300)
    chip = g.blend('07 LOCAL WEAR INPUT',chip,extra,960,0,mode=5)
    # Independently aged exposed steel prevents every chip from looking equally rusty.
    oxide = g.inst('08 OXIDATION FIELD','noise_clouds_2',720,530,params={'scale':('Int1',5),'randomseed':('Int32',691)})
    oxide = g.inst('09 INDEPENDENT AGE','histogram_scan',960,530,{'Input_1':oxide},{'Position':age,'Contrast':('Float1',.85)})
    inner = g.inst('09b SOFTEN CORROSION BOUNDARY','blur_hq',960,780,{'Source':chip},{'Intensity':('Float1',.06),'Quality':('Int1',1)},graph='blur_hq_grayscale')
    inner = g.levels('09c EXPOSED STEEL MARGIN',inner,1200,780,.52,.70)
    rust = g.blend('10 RUST INSIDE CHIPS',inner,oxide,1200,220,mode=3)
    rust = g.blend('10b CONSTRAIN TO LOST PAINT',rust,chip,1440,530,mode=3)
    steel = g.blend('11 REMAINING BARE STEEL',chip,rust,1440,0,mode=2)
    paint = g.levels('12 INTACT PAINT',chip,1200,-220,outlow=1,outhigh=0)
    # Submillimetre halo and lifted rim respond to the same coating boundary.
    halo = g.inst('13 UNDERFILM HALO','blur_hq',1200,500,{'Source':rust},{'Intensity':('Float1',2.2),'Quality':('Int1',1)},graph='blur_hq_grayscale')
    rim = g.inst('14 NARROW LIFTED RIM','blur_hq',1440,300,{'Source':chip},{'Intensity':('Float1',.08),'Quality':('Int1',1)},graph='blur_hq_grayscale')
    rim = g.blend('15 LIFTED ENAMEL RIM',rim,chip,1660,300,mode=2)
    fine = g.inst('16 OXIDE FINE GRAIN','grunge_rust_fine',0,800,params={'balance':('Float1',.5),'contrast':('Float1',.22)})
    pores = g.inst('17 MICRO PITTING','noise_bnw_spots_2',0,1020,params={'scale':('Int1',18),'randomseed':('Int32',271)})
    micro = g.inst('18 ENAMEL ORANGE PEEL','noise_perlin_noise',0,1240,params={'scale':('Int1',480),'randomseed':('Int32',13)})
    scratch = g.inst('19 HANDLING SCRATCHES','grunge_scratches_fine',0,1460,params={'balance':('Float1',.55),'contrast':('Float1',.35),'scratches_amount':('Float1',.24)})
    # Base color uses material reflectance only: no AO or directional shading.
    pc = g.uniform('20 ENAMEL COLOR',(.61,.61,.54,1),1920,-250,tint)
    stain_c = g.uniform('21 OXIDE BLEED COLOR',(.29,.255,.15,1),1920,-20)
    pc = g.blend('22 UNDERFILM DISCOLORATION',pc,stain_c,2150,-250,halo,opacity=.42)
    dirt = g.blend('23 DIRT ON COATING',paint,cloud,1660,600,mode=3)
    dirt_c = g.uniform('24 EMBEDDED DIRT COLOR',(.27,.265,.21,1),1920,230)
    pc = g.blend('25 ACCUMULATED GRIME',pc,dirt_c,2390,-250,dirt,opacity=dirt_amount)
    rc0 = g.uniform('26 DEEP OXIDE',(.095,.037,.018,1),1920,700)
    rc1 = g.uniform('27 OXIDE MIDTONE',(.25,.115,.046,1),1920,920,rust_tint)
    rc = g.blend('28 GRANULAR RUST COLOR',rc0,rc1,2150,700,fine)
    rc2 = g.uniform('29 DRY OXIDE FLECKS',(.38,.205,.08,1),2150,980)
    fleck = g.levels('30 ISOLATED OXIDE HIGHLIGHTS',pores,1920,1210,.64,.85)
    rc = g.blend('31 OXIDE COLOR DEPTH',rc,rc2,2390,700,fleck,opacity=.48)
    sc = g.uniform('32 EXPOSED STEEL F0',(.74,.75,.76,1),2390,400)
    bc = g.blend('33 COATING / BARE STEEL',pc,sc,2640,-250,chip)
    bc = g.blend('34 FINAL ALBEDO',bc,rc,2880,-250,rust)
    # Roughness: independent paint, oxide and steel responses with subtle scratches.
    pr = g.inst('35 PAINT ROUGHNESS RANGE','histogram_range',1920,1550,{'input':cloud},{'range':('Float1',.08),'position':paint_r})
    pr_micro = g.levels('35b SUBTLE MICRO ROUGHNESS',micro,1660,1780,outlow=.44,outhigh=.58)
    pr = g.blend('35c PAINT MICRO REFLECTION',pr,pr_micro,2150,1780,opacity=.3)
    sr = g.levels('36 STEEL ROUGHNESS',scratch,1920,1780,outlow=.24,outhigh=.38)
    rr = g.levels('37 POROUS OXIDE ROUGHNESS',fine,1920,2010,outlow=.71,outhigh=.93)
    rough = g.blend('38 ENAMEL / STEEL ROUGHNESS',pr,sr,2150,1550,chip)
    rough = g.blend('39 OXIDIZED ROUGHNESS',rough,rr,2390,1550,rust)
    # Height uses a 0.6 mm full range: actual layer steps are a fraction of it.
    ph = g.levels('40 PAINT MICRORELIEF',micro,490,950,outlow=.58,outhigh=.60)
    scuff = g.levels('40b FINE ENAMEL SCRATCHES',scratch,240,1460,.68,.85,outlow=0,outhigh=.006)
    ph = g.blend('40c SCRATCHED COATING HEIGHT',ph,scuff,720,1180,mode=2)
    sh = g.levels('41 STEEL MICRORELIEF',scratch,490,1180,outlow=.40,outhigh=.411)
    rh = g.levels('42 OXIDE LAMINATION',fine,490,1410,outlow=.32,outhigh=.47)
    pits = g.levels('43 SMALL CORROSION PITS',pores,490,1640,.4,.8,outlow=.07,outhigh=0)
    rh = g.blend('44 PITTED OXIDE HEIGHT',rh,pits,720,1410,mode=2)
    height = g.blend('45 COATING THICKNESS',ph,sh,960,950,chip)
    height = g.blend('46 OXIDE MICROGEOMETRY',height,rh,1200,950,rust)
    height = g.blend('47 SLIGHTLY RAISED CHIP EDGE',height,rim,1440,950,mode=1,opacity=.08)
    # Keep the final height unblurred. Global blur erases the very microdetail we authored.
    normal = g.inst('49 PHYSICAL OPENGL NORMAL','height_to_normal_world_units',2640,1850,{'input':height},{'surface_size':tile_cm,'height_depth':depth,'normal_format':('Int1',1),'sampling':('Int1',1)},graph='height_to_normal_world_units_2')
    ao = g.inst('50 MICRO AMBIENT OCCLUSION','ambient_occlusion',2640,2130,{'Source':height},{'AO_Spread':('Float1',.018)})
    for i,(name,source,usage) in enumerate([('BaseColor',bc,'baseColor'),('Roughness',rough,'roughness'),('Metallic',steel,'metallic'),('Normal',normal,'normal'),('Height',height,'height'),('AO',ao,'ambientOcclusion'),('WearMask',chip,None),('RustMask',rust,None),('PaintMask',paint,None),('DirtMask',dirt,None)]):
        g.output(name,source,3240,i*240-250,usage)
    g.save()


if __name__=='__main__':
    build()
