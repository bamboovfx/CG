"""归档本轮用户截图、公开作品预览和原片联系表；网络内容只作为参考数据。"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from html import unescape
import hashlib
import json
import re
import shutil
import subprocess
import requests
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
OUT = ROOT / '01_preproduction/references/classroom_research_20260917'
OUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
PAGES = [
    ('ryo_sugiyama', 'https://suggypop.artstation.com/projects/QrXbLx'),
    ('vivek_ranjan', 'https://yakuzaknight99.artstation.com/projects/klN83y'),
    ('nimikko', 'https://nimikko.artstation.com/projects/ZG9O6G'),
    ('gabriel_krausz', 'https://gabrielkrausz.artstation.com/projects/q9d6Nz'),
    ('ben_gibson', 'https://bgibson11.artstation.com/projects/rRgg0J'),
    ('mark_allen', 'https://markallen.artstation.com/projects/zxoV6'),
    ('sayak_pal', 'https://sayakpal.artstation.com/projects/WmxGO3'),
    ('andrea_cantelli', 'https://www.artstation.com/artwork/k545y'),
    ('diaz', 'https://diazdigitalarts.artstation.com/projects/Jr1nAd'),
    ('ykk_crescent', 'https://www.ykkap.co.jp/business/products/window/replacement-parts'),
    ('sanwa_school', 'https://www.sanwa-ss.co.jp/professional/products/000857.html'),
]

def fetch_page(spec):
    """输入已核实的公开页面；保存少量作品预览和溯源，不绕过登录或拒绝访问。"""
    key, url = spec
    record = {'id': key, 'url': url, 'accessed': '2026-09-17', 'images': [],
              'usage': '研究参考，版权归原作者；不用于贴图或重新发布。'}
    try:
        response = requests.get(url, timeout=20)
        record['http_status'] = response.status_code
        response.raise_for_status()
        html = unescape(response.text)
        (OUT / (key + '.html')).write_text(html, encoding='utf-8')
        # ArtStation 个人作品页直接公布作品图片 URL；只读取已返回的页面字段。
        candidates = re.findall(r'https://cdna\.artstation\.com/p/assets/images/[^\s"<>]+', html)
        if not candidates:
            candidates = re.findall(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)', html)
        seen = set()
        for image_url in candidates:
            image_url = image_url.replace('\\/', '/').split('\\')[0]
            stem = image_url.split('?')[0]
            if stem in seen:
                continue
            seen.add(stem)
            if len(record['images']) >= 3:
                break
            image_response = requests.get(image_url, timeout=20)
            if image_response.status_code != 200:
                continue
            ext = '.png' if 'png' in image_response.headers.get('Content-Type', '') else '.jpg'
            path = OUT / (key + '_' + str(len(record['images']) + 1) + ext)
            path.write_bytes(image_response.content)
            try:
                with Image.open(path) as im:
                    width, height = im.size
                if width < 300 or height < 150:
                    continue
            except Exception:
                continue
            record['images'].append({'url': image_url, 'file': path.name, 'size': [width, height],
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    except Exception as exc:
        record['error'] = str(exc)
    return record

def sheet(items, filename, columns=3):
    """输入图片路径与标题；输出仅供检查的等比缩略联系表，原始参考不改写。"""
    tile_w, tile_h = 560, 350
    canvas = Image.new('RGB', (columns * tile_w, ((len(items) + columns - 1) // columns) * tile_h), '#171b20')
    draw = ImageDraw.Draw(canvas)
    for index, (path, title) in enumerate(items):
        im = Image.open(path).convert('RGB')
        im.thumbnail((tile_w - 16, tile_h - 48))
        x, y = (index % columns) * tile_w, (index // columns) * tile_h
        canvas.paste(im, (x + (tile_w - im.width) // 2, y + 4))
        draw.text((x + 10, y + tile_h - 37), title, font=FONT, fill='#eeeeee')
    canvas.save(OUT / filename)

# 保存用户发来的四张原图，避免临时剪贴板清理后丢失依据。
clips = ['eb1de16d-1092-4c5d-9f6f-708a48f37f8a', '4a1fd5e2-9704-4f38-bb02-08f27baa93b0',
         'ae854803-c15f-4d18-8bf0-5ba7a2354ae4', 'b2262cf4-3e9f-4c55-8e02-e22108c89091']
for index, key in enumerate(clips, 1):
    source = Path('C:/Users/xianyi.shi/AppData/Local/Temp') / ('codex-clipboard-' + key + '.png')
    shutil.copy2(source, OUT / ('user_reference_' + str(index) + '.png'))

with ThreadPoolExecutor(max_workers=4) as executor:
    records = list(executor.map(fetch_page, PAGES))
(OUT / 'image_sources.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
items = [(OUT / image['file'], r['id'] + ' / ' + str(i + 1)) for r in records for i, image in enumerate(r['images'])]
if items:
    sheet(items, 'artstation_contact_sheet.jpg')

# 本地正式视频来自既有来源清单；抽帧保留编码黑边且不锐化。
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
video = ROOT / '01_preproduction/references/video/drop_official_1080p.mp4'
frames = []
for seconds in range(100, 176, 5):
    path = OUT / ('film_' + str(seconds) + 's.png')
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(seconds),
                    '-i', str(video), '-frames:v', '1', str(path)], check=True)
    frames.append((path, 'dro:p / ' + str(seconds) + 's'))
sheet(frames, 'film_contact_sheet.jpg', 4)
print(json.dumps({'pages': len(records), 'downloaded_images': len(items), 'film_frames': len(frames),
                  'failures': [{'id': r['id'], 'error': r.get('error')} for r in records if r.get('error')]}, ensure_ascii=False))
