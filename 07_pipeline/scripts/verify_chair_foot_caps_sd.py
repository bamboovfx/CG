"""将原生SBSAR四个表现强度归零，读取4K实际输出检验回到工艺层。"""
from pathlib import Path
import json
import subprocess
import numpy as np
from PIL import Image
from tripo_wood_detail_sd import SD

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '06_review/chair_foot_cap_materials_20261001'
ZERO = ROOT / '07_pipeline/cache/chair_foot_cap_materials_20261001/sd_zero'


def main():
    """输入可编辑SBSAR，渲染同分辨率零表现图，输出蒙版及通道恢复证据。"""
    ZERO.mkdir(parents=True, exist_ok=True)
    cmd = [str(SD / 'sbsrender.exe'), 'render', '--inputs',
        str(ROOT / '02_assets/materials/chair_foot_caps/chair_foot_caps.sbsar'),
        '--output-path', str(ZERO), '--output-name', '{outputNodeName}', '--set-value', '$outputsize@12,12',
        '--engine', 'd3d11', '--output-bit-depth', '16', '--no-report']
    for name in ['Wear', 'Age', 'Scratches', 'Dirt']:
        cmd.extend(['--set-value', name + '@0'])
    done = subprocess.run(cmd, capture_output=True, text=True)
    (ZERO / 'render.log').write_text(done.stdout + done.stderr, encoding='utf-8')
    assert done.returncode == 0, (done.stdout + done.stderr)[-2000:]
    masks = {}; channels = {}
    for name in ['WearMask', 'AgeMask', 'ScratchMask', 'DirtMask']:
        value = np.asarray(Image.open(ZERO / (name + '.png')))
        masks[name] = int(value.max())
        assert masks[name] == 0, (name, masks[name])
    for name in ['BaseColor', 'Roughness', 'Metallic', 'Height', 'Normal', 'AO']:
        a = np.asarray(Image.open(ZERO / ('Process_' + name + '.png'))).astype(np.int32)
        b = np.asarray(Image.open(ZERO / ('Final_' + name + '.png'))).astype(np.int32)
        channels[name] = int(np.abs(a - b).max())
        assert channels[name] <= 2, (name, channels[name])
    audit = {'resolution': 4096, 'zero_masks_max': masks, 'final_vs_process_max': channels, 'passed': True}
    (OUT / 'sd_zero_validation.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print('FOOT_CAP_SD_ZERO ' + json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
