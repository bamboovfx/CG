"""整理实际同光渲染和1:1通道裁片，核对归零恢复；不编辑源材质贴图。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '06_review/chair_metal_layers_20261001'
TEX = ROOT / '02_assets/textures/generated/chair_metal_layers'


def main():
    """输入实际评审PNG，输出分层对照、100%裁片与像素差记录。"""
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 23)
    pairs = [('whole_comparison.jpg', '原材质', '00_before_whole.png', '金属分层材质', '01_after_whole.png'),
        ('rail_comparison.jpg', '仅工艺层', '05_process_rail.png', '工艺＋表现层', '02_after_rail.png')]
    for file, left, a, right, b in pairs:
        canvas = Image.new('RGB', (1600, 658 if 'rail' in file else 950), (24, 24, 24))
        draw = ImageDraw.Draw(canvas)
        for index, (label, name) in enumerate([(left, a), (right, b)]):
            im = Image.open(OUT / name).convert('RGB')
            im.thumbnail((800, canvas.height - 58), Image.Resampling.LANCZOS)
            canvas.paste(im, (index * 800, 58))
            draw.text((index * 800 + 18, 14), label, font=font, fill='white')
        canvas.save(OUT / file, quality=96)
    # 同一实际像素窗口，16位数据图以其完整范围显示，不拉对比度冒充细节。
    canvas = Image.new('RGB', (1536, 1120), (24, 24, 24)); draw = ImageDraw.Draw(canvas)
    names = ['ChipField', 'RustColor', 'RustRoughness', 'RustHeight', 'Process_Roughness', 'ScratchMask']
    for index, name in enumerate(names):
        im = Image.open(TEX / (name + '.png'))
        crop = np.asarray(im.crop((1536, 1536, 2048, 2048)))
        if crop.ndim == 2:
            crop = np.clip(crop.astype(np.float32) / 257, 0, 255).astype(np.uint8)
        tile = Image.fromarray(crop).convert('RGB')
        x = index % 3 * 512; y = index // 3 * 560
        canvas.paste(tile, (x, y + 48)); draw.text((x + 10, y + 10), name + ' / 100%', font=font, fill='white')
    canvas.save(OUT / 'map_100_percent.png')
    a = np.asarray(Image.open(OUT / '06_process_whole.png')).astype(np.int16)
    b = np.asarray(Image.open(OUT / '07_direct_process_whole.png')).astype(np.int16)
    delta = np.abs(a - b)
    audit = {'max_8bit': int(delta.max()), 'mean': float(delta.mean()), 'fraction_gt_2': float((delta > 2).mean())}
    assert audit['max_8bit'] <= 2
    (OUT / 'zero_comparison.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print('CHAIR_METAL_REVIEW ' + json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
