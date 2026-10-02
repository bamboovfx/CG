"""原生Designer金属分层配方：灰白漆工艺、真实锈细节及掉漆／划痕／污渍内容。"""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import xml.etree.ElementTree as E
from PIL import Image
from build_desk_substance import Graph
from tripo_wood_detail_sd import bitmap, colour_levels, SD
from wood_layers_sd import annotate

ROOT = Path(__file__).resolve().parents[2]
MAT = ROOT / '02_assets/materials/chair_metal_layers'
TEX = ROOT / '02_assets/textures/generated/chair_metal_layers'
WORK = ROOT / '07_pipeline/cache/chair_metal_layers_20261001'
SCAN = ROOT / '02_assets/textures/external/polyhaven_chair_metal/rust_coarse_01'


def build():
    """输入原生8K扫描与Adobe节点库，输出4K工艺／表现通道及可编辑SBS/SBSAR。"""
    for folder in [MAT, TEX, WORK]:
        folder.mkdir(parents=True, exist_ok=True)
    g = Graph()
    identifier = 'chair_metal_layers'
    for element in [g.p, g.g]:
        element.find('identifier').set('v', identifier)
    g.p.find('fileUID').set('v', '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, identifier + '20261001')) + '}')
    g.g.find('./attributes/label').set('v', 'Chair metal: process and appearance')
    g.g.find('./attributes/description').set('v', 'Ivory grey enamel on steel. CC0 Rust Coarse 01 original 8K supplies oxide microcolour/roughness/high-pass relief. 4K content tile 0.12m; physical placement remains separate in Blender. Paint and rust metallic=0, exposed steel=1. No lighting baked into colour. Heights interpreted in metres in Blender.')
    paint_r = g.expose('PaintRoughness', 'Paint roughness', .39, '01 Process', .1, .8)
    paint_c = g.expose('PaintColor', 'Grey white enamel', (.69, .70, .665, 1), '01 Process', typ='Float4')
    controls = {k: g.expose(k, k, 1, '02 Appearance') for k in ['Wear', 'Rust', 'Age', 'Scratches', 'Dirt']}
    zero = g.uniform('零值', 0, 0, 0)
    one = g.uniform('平面AO／满值', 1, 0, 0)
    micro = g.inst('工艺／细微喷漆颗粒', 'noise_dirt_3', 0, 0,
        params={'scale': ('Int1', 8), 'randomseed': ('Int32', 101)})
    cloud = g.inst('工艺／微弱涂漆浓淡', 'noise_clouds_2', 0, 0,
        params={'scale': ('Int1', 2), 'randomseed': ('Int32', 118)})
    base = g.uniform('工艺／灰白漆颜色', (.69, .70, .665, 1), 0, 0, exposed=paint_c)
    base = g.blend('工艺／微弱颜色变化', base, g.uniform('工艺／薄漆色', (.66, .67, .637, 1), 0, 0), 0, 0, cloud, opacity=.14)
    rough = g.blend('工艺／基础粗糙度', zero, one, 0, 0, opacity=paint_r)
    rough = g.blend('工艺／微橘皮反射', rough, g.levels('工艺／细部粗糙度', micro, 0, 0, outlow=.34, outhigh=.46), 0, 0, opacity=.18)
    height = g.levels('工艺／微起伏：整幅45微米标尺', micro, 0, 0, outlow=.47, outhigh=.53)
    normal = g.filt('工艺／OpenGL法线', 'normal', 0, 0, {'input1': height}, {'intensity': ('Float1', .12), 'inversedy': ('Bool', 0)}, channels=1)

    # 锈蚀实物只提供多色和微细形态，不沿用任何百叶板宏观形状或大凹凸。
    scan = {name: bitmap(g, SCAN / filename, colour, 13) for name, filename, colour in [
        ('Color', 'rust_coarse_01_diff_8k.jpg', True),
        ('Rough', 'rust_coarse_01_rough_8k.jpg', False),
        ('Height', 'rust_coarse_01_disp_8k.jpg', False)]}
    rust_color = colour_levels(g, scan['Color'], '实物氧化：深褐／赭色／细颗粒',
        (.015, .01, .004), (.46, .25, .11), (.075, .027, .009), (.40, .19, .071))
    rust_rough = g.levels('干燥锈粗糙度', scan['Rough'], 0, 0, .1, .9, .67, .90)
    hp = g.inst('分離实物高频凹蚀', 'highpass', 0, 0, {'Source': scan['Height']},
        {'Radius': ('Float1', 8)}, graph='highpass_grayscale')
    rust_h = g.levels('锈层微起伏：仅局部120微米标尺', hp, 0, 0, .46, .54, .24, .76)
    spots = g.inst('不规则成片剥漆', 'noise_bnw_spots_2', 0, 0,
        params={'scale': ('Int1', 5), 'randomseed': ('Int32', 1721)})
    grain = g.inst('剥漆破碎边缘', 'grunge_rust_fine', 0, 0,
        params={'randomseed': ('Int32', 715)})
    field = g.blend('剥漆边缘复合', spots, grain, 0, 0, opacity=.23)
    field = g.filt('毫米磕碰碎边', 'warp', 0, 0, {'input1': field, 'inputgradient': hp}, {'intensity': ('Float1', .00018)})
    chip = g.levels('掉漆连续细节场', field, 0, 0, .19, .82)
    age = g.levels('漆面氧化雾化细节', cloud, 0, 0, .15, .87, .08, .68)
    scratch = g.inst('细浅交叉划痕', 'pattern_scratches_generator', 0, 0,
        params={'spline_number': ('Int1', 24), 'spline_scale': ('Float1', .18),
        'spline_width': ('Float1', 1.4), 'spline_width_in_pixel': ('Bool', 1),
        'spline_rotation_random': ('Float1', .84), 'spline_scale_random': ('Float1', .7),
        'spline_distortion_random': ('Float1', .07), 'randomseed': ('Int32', 1017)}, graph='scratches_generator')
    dirt = g.levels('稀疏附着脏点', grain, 0, 0, .74, .88)
    signals = {'ChipField': chip, 'RustColor': rust_color, 'RustRoughness': rust_rough,
        'RustHeight': rust_h, 'AgeMask': age, 'ScratchMask': scratch, 'DirtMask': dirt}
    for k, param in [('ChipField', 'Wear'), ('AgeMask', 'Age'), ('ScratchMask', 'Scratches'), ('DirtMask', 'Dirt')]:
        signals[k] = g.blend(k + '独立强度', zero, signals[k], 0, 0, opacity=controls[param])
    signals['RustHeight'] = g.blend('锈高度独立强度', g.uniform('锈高度中点', .5, 0, 0), rust_h, 0, 0, opacity=controls['Rust'])
    outputs = {'Process_BaseColor': (base, 'baseColor'), 'Process_Roughness': (rough, 'roughness'),
        'Process_Metallic': (zero, 'metallic'), 'Process_Height': (height, 'height'),
        'Process_Normal': (normal, 'normal'), 'Process_AO': (one, 'ambientOcclusion')}
    outputs.update({k: (v, None) for k, v in signals.items()})
    # SD内也可预览完整分层；这里是通用样片，资产损伤位置由Blender另行限定。
    lost = g.levels('SD样片／剥漆阈值', chip, 0, 0, .66, .72)
    lost = g.blend('SD样片／掉漆强度', zero, lost, 0, 0, opacity=controls['Wear'])
    oxide = g.blend('SD样片／锈覆盖', zero, lost, 0, 0, opacity=controls['Rust'])
    fc = g.blend('SD样片／漆氧化', base, g.uniform('SD样片／老漆色', (.60, .62, .56, 1), 0, 0), 0, 0, signals['AgeMask'], opacity=.40)
    fc = g.blend('SD样片／露钢', fc, g.uniform('SD样片／钢灰', (.24, .25, .25, 1), 0, 0), 0, 0, lost)
    fc = g.blend('SD样片／锈多色', fc, rust_color, 0, 0, oxide)
    fc = g.blend('SD样片／脏渍', fc, g.uniform('SD样片／灰褐脏渍', (.19, .177, .142, 1), 0, 0), 0, 0, signals['DirtMask'], opacity=.5)
    fr = g.blend('SD样片／漆老化粗糙度', rough, g.uniform('雾化粗糙度', .52, 0, 0), 0, 0, signals['AgeMask'])
    fr = g.blend('SD样片／锈粗糙度', fr, rust_rough, 0, 0, oxide)
    fr = g.blend('SD样片／划痕粗糙度', fr, g.uniform('划痕粗糙度', .57, 0, 0), 0, 0, signals['ScratchMask'])
    fr = g.blend('SD样片／脏渍粗糙度', fr, g.uniform('干燥脏渍粗糙度', .79, 0, 0), 0, 0, signals['DirtMask'])
    fm = g.blend('SD样片／裸钢与漆区', zero, one, 0, 0, lost)
    fm = g.blend('SD样片／锈非金属', fm, zero, 0, 0, oxide)
    fh = g.blend('SD样片／漆口浅台阶', height, g.uniform('露底浅凹', .28, 0, 0), 0, 0, lost)
    fh = g.blend('SD样片／锈蚀微起伏', fh, signals['RustHeight'], 0, 0, oxide)
    fn = g.filt('SD样片／最终OpenGL法线', 'normal', 0, 0, {'input1': fh}, {'intensity': ('Float1', .12), 'inversedy': ('Bool', 0)}, channels=1)
    outputs = {k: (v[0], None) for k, v in outputs.items()}
    outputs.update({'Final_BaseColor': (fc, 'baseColor'), 'Final_Roughness': (fr, 'roughness'),
        'Final_Metallic': (fm, 'metallic'), 'Final_Height': (fh, 'height'),
        'Final_Normal': (fn, 'normal'), 'Final_AO': (one, 'ambientOcclusion'), 'Preview_ChipMask': (lost, None), 'Preview_RustMask': (oxide, None)})
    for name, (signal, usage) in outputs.items():
        g.output(name, signal, 0, 0, usage)
    annotate(g)
    path = MAT / (identifier + '.sbs')
    E.indent(g.p)
    E.ElementTree(g.p).write(path, encoding='utf-8', xml_declaration=True)
    commands = [
        [str(SD / 'sbscooker.exe'), '--inputs', str(path), '--output-path', str(MAT), '--alias', 'sbs://' + str(SD / 'resources/packages')],
        [str(SD / 'sbsrender.exe'), 'render', '--inputs', str(path.with_suffix('.sbsar')), '--output-path', str(TEX),
            '--output-name', '{outputNodeName}', '--set-value', '$outputsize@12,12', '--engine', 'd3d11', '--output-bit-depth', '16', '--no-report']]
    for index, cmd in enumerate(commands):
        done = subprocess.run(cmd, capture_output=True, text=True)
        (WORK / f'sd_{index}.log').write_text(done.stdout + done.stderr, encoding='utf-8')
        if done.returncode:
            raise RuntimeError((done.stdout + done.stderr)[-3000:])
    files = []
    for p in TEX.glob('*.png'):
        with Image.open(p) as im:
            assert im.size == (4096, 4096)
            files.append({'name': p.name, 'pixels': list(im.size), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest = {'source': str(path.relative_to(ROOT)), 'files': files, 'tile_m': .12,
        'resolution': 4096, 'scan_input_resolution': 8192, 'normal': 'OpenGL',
        'scan_source': 'https://polyhaven.com/a/rust_coarse_01', 'scan_license': 'CC0-1.0',
        'positioning': 'Asset-specific analytic 3D envelopes; content tile separate from placement',
        'controls': list(controls), 'nodes': len(g.nodes)}
    (TEX / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('CHAIR_METAL_SD ' + json.dumps({'nodes': len(g.nodes), 'outputs': len(files)}), flush=True)


if __name__ == '__main__':
    build()
