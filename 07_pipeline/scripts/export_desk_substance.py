"""Render the native desk Substance into repeatable 2K/4K PBR texture sets.

Inputs: compiled SBSAR and the two documented weathering presets.
Outputs: generated textures, hashes, channel metadata and parameter checks.
"""
from pathlib import Path
import subprocess
import json
import hashlib
from datetime import datetime, timezone
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SD = Path('D:/Program Files/Adobe/Adobe Substance 3D Designer')
SOURCE = ROOT/'02_assets/materials/school_desk/school_desk_painted_steel.sbsar'
OUT = ROOT/'02_assets/textures/generated/school_desk_sd'
PRESETS = {
    'frame': {'Wear':.36, 'Age':.60, 'DirtAmount':.14, 'ChipScale':3, 'CrackAmount':.46},
    'brace': {'Wear':.56, 'Age':.75, 'DirtAmount':.20, 'ChipScale':3, 'CrackAmount':.52},
}
CHANNELS = ('BaseColor','Roughness','Metallic','Height','Normal','AO',
            'WearMask','RustMask','PaintMask','DirtMask','CrackMask')
LAYER_CHANNELS = tuple(layer+channel for layer in ('Paint','Steel','Rust')
                       for channel in ('BaseColor','Roughness','Height'))


def render(name, size, params, channels=()):
    """Render one parameter set with Adobe's engine and preserve its exact log."""
    dest = OUT/name/('4k' if size==12 else '2k' if size==11 else 'test')
    dest.mkdir(parents=True, exist_ok=True)
    args = [str(SD/'sbsrender.exe'),'render','--inputs',str(SOURCE),
            '--output-path',str(dest),'--output-name','{outputNodeName}',
            '--set-value',f'$outputsize@{size},{size}', '--engine','d3d11',
            '--output-bit-depth','16','--no-report']
    for key,value in params.items(): args += ['--set-value',f'{key}@{value}']
    for channel in channels or CHANNELS: args += ['--input-graph-output',channel]
    log = ROOT/f'07_pipeline/cache/sd_{name}_{size}.log'
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,check=True)
    print(f'RENDERED {name} {2**size}px',flush=True)
    return dest


def mask(path):
    """Read a 16-bit grayscale output as a normalized float mask."""
    return np.asarray(Image.open(path),dtype=np.float32)/65535


def check(dest):
    """Check layer partition, roughness and boundary continuity in a rendered set."""
    wear = mask(dest/'WearMask.png'); rust = mask(dest/'RustMask.png')
    metal = mask(dest/'Metallic.png'); paint = mask(dest/'PaintMask.png')
    rough = mask(dest/'Roughness.png')
    errors = float(np.max(np.abs(paint+rust+metal-1)))
    assert errors < .003, f'Layer partition error: {errors}'
    assert np.max(rust-wear)<.001, 'Rust escaped chipped coating'
    cracks = mask(dest/'CrackMask.png')
    assert np.max(cracks-paint)<.001, 'Cracks escaped intact paint'
    assert np.mean(rough[rust>.95])>.68, 'Oxide is implausibly glossy'
    # Seam differences should behave like neighboring interior pixel differences.
    height = mask(dest/'Height.png')
    seam = float((np.mean(abs(height[:,0]-height[:,-1]))+np.mean(abs(height[0]-height[-1])))/2)
    interior = float((np.mean(abs(np.diff(height,axis=0)))+np.mean(abs(np.diff(height,axis=1))))/2)
    return {'coating_loss_fraction':float(wear.mean()), 'oxide_fraction':float(rust.mean()),
            'bare_metal_fraction':float(metal.mean()), 'layer_partition_max_error':errors,
            'height_seam_mean_difference':seam,'height_interior_mean_difference':interior,
            'crack_mask_mean':float(cracks.mean()),
            'dimensions':list(Image.open(dest/'Height.png').size)}


def main():
    """Export production textures and collect traceable, measured delivery metadata."""
    results={}
    for name,params in PRESETS.items():
        for size in (11,12):
            dest=render(name,size,params)
            results[f'{name}/{2**size}']=check(dest)
    # Change Age alone: chip distribution must remain identical.
    young=render('age_check',9,{**PRESETS['frame'],'Age':.20},('WearMask','RustMask'))
    old=render('age_check_old',9,PRESETS['frame'],('WearMask','RustMask'))
    independent=np.array_equal(np.asarray(Image.open(young/'WearMask.png')),np.asarray(Image.open(old/'WearMask.png')))
    assert independent, 'Age changed coating loss'
    assert mask(young/'RustMask.png').mean()<mask(old/'RustMask.png').mean(), 'Age does not increase oxidation'
    # Native layer endpoints preserve physical scale while asset wear uses its original UVs.
    for size in (11,12): render('layers',size,{'Wear':0,'Age':.6,'CrackAmount':.46},LAYER_CHANNELS)
    files=[]
    for name in (*PRESETS,'layers'):
        for file in sorted((OUT/name).rglob('*.png')):
            files.append({'path':file.relative_to(ROOT).as_posix(), 'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                          'size':list(Image.open(file).size), 'colorspace':'sRGB' if file.stem.endswith('BaseColor') else 'Non-Color',
                          'bit_depth':int(file.read_bytes()[24])})
    report={'asset':'school_desk_painted_steel','created_utc':datetime.now(timezone.utc).isoformat(),
            'method':'Substance Designer native procedural node graph; no diffusion or source photographs used as textures',
            'seed':3087,'tile_width_m':.2,'height_range_m':.0006,'normal_convention':'OpenGL',
            'presets':PRESETS,'validation':results,'age_independence_verified':independent,
            'source':SOURCE.relative_to(ROOT).as_posix(),'reference':'https://andreariccardi.artstation.com/projects/QzmB2B',
            'reference_use':'Previous task inspected artist reference images in Chrome; native textures do not copy those images. Appearance authority: supplied props_01 desk reference.',
            'status':'material lookdev, pending visual acceptance; scene integration not approved', 'files':files}
    (OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)


if __name__=='__main__':
    main()
