"""通过 PureRef 原生重开/导出验证画板，检查来源文件与排版矩形。

导出到项目缓存仅用于核验；正式交付仅一个 .pur 和来源索引。
"""
import hashlib
import json
import argparse
from pathlib import Path
import shutil

from PIL import Image, ImageOps, ImageChops

from build_pureref_board import ROOT, OUT, CACHE, BOARD, run_cli


def pixels(path):
    """输入图片路径，输出与清点阶段一致的解码像素指纹。"""
    with Image.open(path) as raw:
        im=ImageOps.exif_transpose(raw).convert('RGBA')
        return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()


def converted_match(source, target):
    """验证 Qt 色彩管理/预乘透明度的导出差异；允许最多1级量化误差。"""
    with Image.open(source) as raw, Image.open(target) as exported:
        if raw.size != exported.size:
            return None
        gamma=raw.info.get('gamma')
        if gamma and raw.info.get('chromaticity') == (0.3127,0.329,0.64,0.33,0.3,0.6,0.15,0.06):
            lut=[]
            for value in range(256):
                linear=(value/255)**(1/gamma)
                srgb=12.92*linear if linear<=0.0031308 else 1.055*linear**(1/2.4)-0.055
                lut.append(round(255*srgb))
            expected=raw.convert('RGB').point(lut*3)
            if max(high for low,high in ImageChops.difference(expected,exported.convert('RGB')).getextrema())<=1:
                return 'metadata_gamma_to_srgb'
        if raw.mode=='RGBA':
            # Qt 的原生导出保留了预乘RGB；不更改源文件或画板图片。
            expected=Image.merge('RGBA',[ImageChops.multiply(c,raw.getchannel('A')) for c in raw.convert('RGB').split()]+[raw.getchannel('A')])
            if max(high for low,high in ImageChops.difference(expected,exported.convert('RGBA')).getextrema())<=1:
                return 'premultiplied_alpha_export'
    return None


def verify(reuse_export=False):
    """核对全部原图、独立导出数量和内容；通过后复制原生候选到正式位置。"""
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    nodes=json.loads((CACHE/'layout.json').read_text(encoding='utf-8'))
    rectangles=[]
    for node in nodes:
        rectangles.append((node['x']-node['width']/2,node['y']-node['height']/2,
                           node['x']+node['width']/2,node['y']+node['height']/2,node['id']))
    overlaps=[]
    for i,a in enumerate(rectangles):
        for b in rectangles[i+1:]:
            if min(a[2],b[2])-max(a[0],b[0])>2 and min(a[3],b[3])-max(a[1],b[1])>2:
                overlaps.append((a[4],b[4]))
    if overlaps: raise RuntimeError(f'排版重叠: {overlaps[:20]}')
    changed=[]
    for item in manifest['images']:
        for original in item['originals']:
            if hashlib.sha256((ROOT/original['path']).read_bytes()).hexdigest()!=original['sha256']:
                changed.append(original['path'])
    if changed: raise RuntimeError(f'原图发生变化，需重新清点: {changed}')
    exported=CACHE/'verification_export'
    exported.mkdir(exist_ok=True)
    if any(exported.iterdir()) and not reuse_export: raise RuntimeError('导出验证目录应为空')
    if not reuse_export:
        run_cli([f'load;{CACHE}/drop_board_candidate.pur',f'exportImages;{exported};false;%2_%0','exit'],timeout=480)
    files=list(exported.glob('*.png'))
    print(f'EXPORT {len(files)} / expected {len(nodes)}',flush=True)
    if len(files)!=len(nodes): raise RuntimeError('原生导出图片数量不匹配')
    # 标题与图注为SVG。只解码实际参考导出的PNG，逐张核对像素，避免重算文字图。
    fingerprints=set()
    for path in files:
        name=path.stem
        if any(token in name for token in ['caption_R','group_','section_','board_guide']):
            continue
        fingerprints.add(pixels(path))
    missing=[]; conversions=[]; exact=0
    for item in manifest['images']:
        if item['pixel_sha256'] in fingerprints:
            exact+=1
            continue
        candidates=list(exported.glob('*_'+Path(item['path']).stem+'.png'))
        match=None
        for target in candidates:
            match=converted_match(ROOT/item['path'],target)
            if match: break
        if match:
            conversions.append({'path':item['path'],'verified_transform':match,'maximum_quantization_error':1})
        else:
            missing.append(item['path'])
    if missing:
        (OUT/'pixel_mismatches.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),encoding='utf-8')
        raise RuntimeError(f'有 {len(missing)} 张原生导出像素不同，需审查（可能是色彩配置转换）')
    if BOARD.exists(): raise FileExistsError('正式场景已存在，不覆盖用户可能的修改')
    shutil.copy2(CACHE/'drop_board_candidate.pur',BOARD)
    report={'date':'2026-09-28','status':'technical-pass','native_reopened':True,
            'images_exported':len(files),'expected_native_items':len(nodes),'references_verified':len(manifest['images']),
            'exact_pixel_matches':exact,'metadata_or_alpha_conversion_verified':conversions,
            'original_files_hash_verified':manifest['reference_files'],'overlap_count':0,
            'board_bytes':BOARD.stat().st_size,'board_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),
            'gui_review':'pending'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-export',action='store_true')
    verify(parser.parse_args().reuse_export)
