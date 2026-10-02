"""在既有 SBS 上增补特写细节，保留原图连接、参数与可编辑原生节点。

输入：首次运行时快照的课桌 SBS。输出：cache 暂存 SBS，审核后才更新固定源。
新增：多尺度片状锈、颗粒孔蚀、漆面擦痕与粗糙度、独立细节控制。
"""
from pathlib import Path
import xml.etree.ElementTree as E
import shutil
from build_desk_substance import Graph, put

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '07_pipeline/cache/desk_sd_closeup'
SOURCE = ROOT / '02_assets/materials/school_desk/school_desk_painted_steel.sbs'
CACHE.mkdir(parents=True, exist_ok=True)
BASE = CACHE / 'before_refinement.sbs'
if not BASE.exists():
    shutil.copy2(SOURCE, BASE)


def open_existing():
    """输入固定快照路径；恢复 Graph 编辑器字段，返回可追加节点的已有图。"""
    g = Graph.__new__(Graph)
    g.p = E.parse(BASE).getroot()
    g.g = g.p.find('./content/graph')
    g.deps = g.p.find('dependencies')
    g.depmap = {d.find('filename').get('v').removeprefix('sbs://').removesuffix('.sbs'): int(d.find('uid').get('v')) for d in g.deps}
    g.nodes = g.g.find('compNodes')
    g.inputs = g.g.find('paraminputs')
    g.outs = g.g.find('graphOutputs')
    g.gui = g.g.find('GUIObjects')
    g.roots = g.g.find('./root/rootOutputs')
    g.i = max(int(e.get('v')) for e in g.p.iter('uid')) + 100
    g.labels = []
    return g


def handle(g, x, y):
    """输入原图节点坐标；返回节点及其输出端口，避免依赖变化的全局 ID。"""
    n = next(n for n in g.nodes if n.find('./GUILayout/gpos').get('v') == f'{x} {y} 0')
    o = n.find('./compOutputs/compOutput')
    return n, (int(n.find('uid').get('v')), int(o.find('uid').get('v')), int(o.find('comptype').get('v')))


def set_parameter(g, node, name, spec):
    """输入节点、参数名与类型值；替换同名参数，其余参数保持不变。"""
    pp = node.find('./compImplementation/*/parameters')
    for p in list(pp):
        if p.find('name').get('v') == name:
            pp.remove(p)
    g.param(pp, name, spec)


def reroute(g, old, new, original_nodes):
    """输入旧/新输出与原节点范围；仅重接旧下游，避免追加分支自连接。"""
    for n in original_nodes:
        for c in n.findall('./connections/connection'):
            if c.find('connRef').get('v') == str(old[0]):
                c.find('connRef').set('v', str(new[0]))
                c.find('connRefOutput').set('v', str(new[1]))


def main():
    """增补物理细节并保存到暂存目录；返回值为空。"""
    g = open_existing()
    originals = list(g.nodes)
    # 默认是适合观察剥漆结构的材质球；资产接入另用保留位置的遮罩。
    for p in g.inputs:
        key = p.find('identifier').get('v')
        if key in {'Wear': .43, 'Age': .48, 'PaintRoughness': .49}:
            p.find('defaultValue')[0].set('v', str({'Wear': .43, 'Age': .48, 'PaintRoughness': .49}[key]))
    grain_amount = g.expose('RustMicroDepth', 'Oxide micro relief', .75, '04 Closeup detail', 0, 1)
    scratch_amount = g.expose('ScratchAmount', 'Paint handling scratches', .24, '04 Closeup detail', 0, 1)
    peel_amount = g.expose('PaintMicroRoughness', 'Enamel micro roughness', .18, '04 Closeup detail', 0, .5)
    # 模糊后再轻微扭曲，避免旧图盐粒状的剥落边缘；保持可调的片区尺度。
    set_parameter(g, handle(g, 240, -280)[0], 'Intensity', ('Float1', 2.1))
    set_parameter(g, handle(g, 260, 0)[0], 'intensity', ('Float1', .0009))
    set_parameter(g, handle(g, 960, 530)[0], 'Contrast', ('Float1', .93))
    # 三个独立频段分别表现氧化层、孔蚀与微颗粒。
    coarse = g.inst('51 OXIDE PLATELETS 2-8mm', 'noise_clouds_2', 0, 2400, params={'scale': ('Int1', 6), 'randomseed': ('Int32', 841)})
    meso = g.inst('52 MESOSCALE CORROSION', 'noise_perlin_noise', 0, 2630, params={'scale': ('Int1', 45), 'randomseed': ('Int32', 459)})
    powder = g.inst('53 SUB-MM OXIDE GRAIN', 'noise_perlin_noise', 0, 2860, params={'scale': ('Int1', 160), 'randomseed': ('Int32', 924)})
    colorfield = g.blend('54 LAYERED OXIDE VARIATION', coarse, meso, 260, 2400, opacity=.32)
    colorfield = g.levels('55 OXIDE COLOR RANGE', colorfield, 490, 2400, .22, .74)
    # 原来的深锈/中锈两色仍然保留，只替换其颗粒遮罩。
    rustcolor = handle(g, 2150, 700)[0]
    for c in rustcolor.findall('./connections/connection'):
        if c.find('identifier').get('v') == 'opacity':
            c.find('connRef').set('v', str(colorfield[0])); c.find('connRefOutput').set('v', str(colorfield[1]))
    fleck = handle(g, 1920, 1210)[0]
    set_parameter(g, fleck, 'levelinlow', ('Float4', (.53, .53, .53, 0)))
    set_parameter(g, fleck, 'levelinhigh', ('Float4', (.74, .74, .74, 1)))
    # 真实高度总量仍为 0.6mm；氧化表面的大中小起伏不会变成厘米级岩石。
    rh = g.levels('56 CORRODED LAYER HEIGHT', coarse, 720, 2400, outlow=.32, outhigh=.48)
    mh = g.levels('57 MESOSCALE HEIGHT', meso, 720, 2630, outlow=.29, outhigh=.51)
    rh = g.blend('58 LAMINATED OXIDE HEIGHT', rh, mh, 960, 2400, opacity=.38)
    pit = g.levels('59 FINE PORE DEPTH', powder, 720, 2860, .27, .70, 0, .045)
    rh = g.blend('60 SUBTRACT CORROSION PORES', rh, pit, 1200, 2400, mode=2, opacity=grain_amount)
    reroute(g, handle(g, 720, 1410)[1], rh, originals)
    roughfield = g.blend('61 OXIDE ROUGHNESS GRAINS', colorfield, powder, 1440, 2630, opacity=.4)
    rr = g.levels('62 OXIDE ROUGHNESS 0.66-0.94', roughfield, 1660, 2630, outlow=.66, outhigh=.94)
    reroute(g, handle(g, 1920, 2010)[1], rr, originals)
    # 漆面的微粗糙度与凹陷不共用锈蚀噪声，保留不同材料反射。
    oldpr = handle(g, 1920, 1550)[1]
    micro = handle(g, 0, 1240)[1]
    mr = g.levels('63 ENAMEL ORANGE PEEL ROUGHNESS', micro, 1920, 2400, outlow=.34, outhigh=.64)
    pr = g.blend('64 INDEPENDENT PAINT MICROFINISH', oldpr, mr, 2150, 2400, opacity=peel_amount)
    reroute(g, oldpr, pr, originals)
    # 擦痕偏细且浅；强度公开，不把所有划痕都直接变成生锈缺口。
    scr = handle(g, 0, 1460)[1]
    scr = g.levels('65 SPARSE HANDLING MARKS', scr, 1920, 2860, .60, .88, 0, .02)
    phold = handle(g, 490, 950)[1]
    ph = g.blend('66 FINE SCRATCHES IN ENAMEL', phold, scr, 2150, 2860, mode=2, opacity=scratch_amount)
    reroute(g, phold, ph, originals)
    # 用分区标题保留图内说明，新增节点注释与原图风格一致。
    for title, x, y in g.labels:
        q = put(g.gui, 'GUIObject'); put(q, 'type', 'COMMENT')
        gl = put(q, 'GUILayout'); put(gl, 'gpos', f'{x-65} {y-90} -100'); put(gl, 'size', '205 52')
        put(q, 'GUIName', ''); put(q, 'uid', g.uid()); put(q, 'title', title)
        put(q, 'frameColor', '0.22 0.14 0.08 0.8'); put(q, 'isTitleVisible', 1); put(q, 'isFrameVisible', 1)
    desc = g.g.find('./attributes/description')
    desc.set('v', desc.get('v') + ' Closeup refinement 2026-09-09: three oxide scales, pore depth, enamel micro roughness and handling marks. 4K master / 20cm tile. Native procedural nodes only; no artist images used as textures.')
    E.indent(g.p)
    dest = CACHE / SOURCE.name
    E.ElementTree(g.p).write(dest, encoding='utf-8', xml_declaration=True)
    print(f'STAGED {dest}: {len(g.nodes)} nodes / {len(g.inputs)} inputs')


if __name__ == '__main__':
    main()
