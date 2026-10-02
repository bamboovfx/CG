"""生成后墙书法纸张图集；只制作新贴图，不修改原片参考图。"""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
OUT = ROOT / '02_assets/textures/authored/rear_classroom_20260917'
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(1709)


def sheet(word, variation):
    """输入竖排词语和变体编号；返回带轻微纸色与墨迹变化的 512×704 纸张图。"""
    h, w = 704, 512
    grain = RNG.normal(0, 1.25, (h, w, 1))
    yy, xx = np.mgrid[:h, :w]
    edge = 2.0 * (np.abs(xx-w/2)/(w/2))**8 + 1.5 * (np.abs(yy-h/2)/(h/2))**8
    rgb = np.clip(np.array([224, 220, 204])[None, None, :] + grain - edge[:, :, None], 0, 255).astype('uint8')
    paper = Image.fromarray(rgb)
    ink = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(ink)
    size = 322 if len(word) == 1 else 260
    font = ImageFont.truetype('C:/Windows/Fonts/simkai.ttf', size)
    centers = [337] if len(word) == 1 else [209, 467]
    for ch, cy in zip(word, centers):
        box = draw.textbbox((0, 0), ch, font=font)
        x = (w-(box[2]-box[0]))/2 - box[0] + int(RNG.integers(-12, 13))
        y = cy-(box[3]-box[1])/2-box[1] + int(RNG.integers(-7, 8))
        draw.text((x, y), ch, font=font, fill=int(RNG.integers(226, 250)))
    # 小幅整张转动和墨色不均仅用于打破完全一致的复制感。
    ink = ink.rotate(float(RNG.uniform(-2.0, 2.0)), resample=Image.Resampling.BICUBIC)
    alpha = np.asarray(ink).astype(float) / 255
    alpha *= np.clip(RNG.normal(.98, .023, (h, w)), .85, 1)
    paper.paste(Image.new('RGB', (w, h), (27, 30, 25)), (0, 0), Image.fromarray((alpha*255).astype('uint8')))
    return paper


# 6 列墨迹变体 × 5 行词语；图集 UV 与后墙模型共用此约定。
words = ['大', '光', '進歩', '未来', '花']
atlas = Image.new('RGB', (4092, 4095), (224, 220, 204))
for row, word in enumerate(words):
    for col in range(6):
        atlas.paste(sheet(word, col).resize((682, 819), Image.Resampling.LANCZOS), (col*682, row*819))
path = OUT / 'calligraphy_atlas_color.png'
atlas.save(path)
manifest = {'type': 'authored graphic texture, not a photograph or scanned PBR',
            'font': 'Windows KaiTi / simkai.ttf', 'seed': 1709,
            'words': words, 'grid': [6,5], 'size': list(atlas.size),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'reference': 'User dro:p rear classroom frame; layout interpretation, not an exact tracing',
            'micro_surface': '../teaching_rebuild/paper_rough.png + paper_height.png'}
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print('REAR_TEXTURES_READY', str(path))
