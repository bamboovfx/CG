"""Download selected public study references and CC0 textures with provenance.

No credentials or browser cookies are used. Source imagery is reference-only.
Poly Haven API credit: Powered by Poly Haven (https://polyhaven.com).
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote
from html import unescape
import requests
import re
import json
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parents[2]
HEADERS={'User-Agent':'ShotTestReferenceStudy/1.0 (Powered by Poly Haven)'}
REF=ROOT/'01_preproduction/references'

def download(url,path):
    """Download a public URL atomically to path; return size and SHA256 metadata."""
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        r=requests.get(url,headers=HEADERS,timeout=60);r.raise_for_status()
        temp=path.with_suffix(path.suffix+'.part');temp.write_bytes(r.content);temp.replace(path)
    data=path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def reference(item):
    """Fetch one selected reference and preserve its source page and intended use."""
    try:
        item.update(download(item['image_url'],ROOT/item['path']))
        item['status']='downloaded'
    except Exception as exc:item['status']='failed';item['error']=str(exc)
    return item

page='https://www.stashmedia.tv/watch-tasuku-nakagawas-animated-short-film-drop/'
html=requests.get(page,headers=HEADERS,timeout=30).text
refs=[]
for tag in re.findall(r'<img[^>]+>',html):
    if 'alt="dro:p short film' not in tag:continue
    candidates=re.findall(r'(https://[^\s,\"]+)\s+(\d+)w',tag)
    url=max(candidates,key=lambda a:int(a[1]))[0] if candidates else re.search(r'src="([^"]+)"',tag)[1]
    i=len(refs)+1
    refs.append({'id':f'film_{i:02d}','image_url':unescape(url),'page_url':page,
      'path':f'01_preproduction/references/film/drop_stash_still_{i:02d}.png',
      'use':'Original-film visual reference. Editorial still order is NOT verified cut order.',
      'rights':'Reference only; Tasuku Nakagawa / publisher. Not a CC0 texture.'})

extra=[
('architecture_01','https://www.maniwa.or.jp/upload/spot/52/img_2.jpg','https://www.maniwa.or.jp/web/?c=spot-2&pk=52','Timber floor, repeated furniture depth; architecture reference only.'),
('architecture_02','https://www.okayama-kanko.jp/lsc/upfile/spot/0001/0842/10842_4_l.jpg','https://www.okayama-kanko.jp/spot/detail_10842.html','Preserved school classroom, joinery and patina; do not copy historic all-wood furniture into hero shot.'),
('architecture_03','https://www.sena-vision.jp/chiikishigen/item_images/4da50bbfac110_2_l.jpg','https://www.sena-vision.jp/tourism/detail/4da50bbfac110/','Window rhythm and school interior details.'),
('props_01','https://aita.ocnk.net/data/aita/product/20160220_800188.JPG','https://aita.ocnk.net/product/3087','Steel-tube desk and plywood chair proportions, feet, rust and edge wear.'),
('props_02','https://livedoor.sp.blogimg.jp/b2_ndline/imgs/6/c/6cbb6828.jpg','https://blog.livedoor.jp/b2_ndline/archives/27325918.html','595 x 400 x 700 mm desk; chair frame and tray construction.'),
('props_03','https://okashi-to-watashi.jp/img/posts/upload/%E2%91%A1%E3%82%B5%E3%82%AF%E3%83%9E%E5%BC%8F%E3%83%89%E3%83%AD%E3%83%83%E3%83%97%E3%82%B9%E3%80%80%E5%A4%A7.jpg','https://okashi-to-watashi.jp/post/1728','Vintage red candy tin: rolled rim, cylindrical cap, label wear; not proof of exact original-film branding.')]
for id,url,src,use in extra:
    folder=id.split('_')[0]
    refs.append({'id':id,'image_url':url,'page_url':src,'path':f'01_preproduction/references/{folder}/{id}.jpg','use':use,'rights':'Reference only; rights remain with source owner.'})
with ThreadPoolExecutor(max_workers=5) as pool:refs=list(pool.map(reference,refs))
(REF/'reference_manifest.json').write_text(json.dumps({'date':'2026-09-08','references':refs},ensure_ascii=False,indent=2),encoding='utf-8')
print('References:',[(x['id'],x['status']) for x in refs],flush=True)

def poly_asset(spec):
    """Download selected map types from the official files endpoint and check MD5."""
    slug,res,usage=spec
    files=requests.get(f'https://api.polyhaven.com/files/{slug}',headers=HEADERS,timeout=30).json()
    folder=ROOT/'02_assets/textures/polyhaven'/slug/res
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'source_files.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
    rows=[]
    for channel in ['diff','rough','nor_gl']:
        api_channel={'diff':'Diffuse','rough':'Rough','nor_gl':'nor_gl'}[channel]
        variants=files.get(api_channel,{}).get(res,{})
        fmt='jpg' if channel in ['diff','rough'] and 'jpg' in variants else ('png' if 'png' in variants else 'exr')
        if fmt not in variants:raise RuntimeError(f'{slug}: missing {channel}/{res}')
        rec=variants[fmt];path=folder/Path(unquote(urlparse(rec['url']).path)).name
        row=download(rec['url'],path)
        if rec.get('md5') and hashlib.md5(path.read_bytes()).hexdigest()!=rec['md5']:raise RuntimeError('Asset checksum mismatch: '+str(path))
        rows.append(dict(row,channel=channel,url=rec['url'],md5=rec.get('md5')))
    return {'id':slug,'provider':'Poly Haven','resolution':res,'usage':usage,'license':'CC0','page_url':f'https://polyhaven.com/a/{slug}','files':rows}

assets=[]
with ThreadPoolExecutor(max_workers=3) as pool:
    for item in pool.map(poly_asset,[('old_wooden_floor_03','4k','Continuous floor UV, 1.2 m source tile'),('plywood','4k','Desk and chair plywood faces'),('painted_plaster_wall','2k','Painted classroom walls, tinted sage/ivory')]):
        assets.append(item);print('PBR:',item['id'],flush=True)

# Resolve ambientCG download anchors from its public page, rather than guess CDN paths.
slug='Fabric030';src=f'https://ambientcg.com/view?id={slug}'
markup=requests.get(src,headers=HEADERS,timeout=30).text
links=[unescape(x) for x in re.findall(r'href="([^"]+)"',markup)]
link=next((x for x in links if '2K-JPG' in x and ('.zip' in x or 'download' in x)),None)
if link:
    if link.startswith('/'):link='https://ambientcg.com'+link
    folder=ROOT/'02_assets/textures/ambientcg'/slug/'2k'
    row=download(link,folder/(slug+'_2K-JPG.zip'))
    with zipfile.ZipFile(ROOT/row['path']) as z:
        for entry in z.infolist():
            target=(folder/entry.filename).resolve()
            if not target.is_relative_to(folder.resolve()):raise RuntimeError('Unsafe archive path')
        z.extractall(folder)
    assets.append({'id':slug,'provider':'ambientCG','resolution':'2k','usage':'Curtain weave and roughness','license':'CC0','page_url':src,'files':[row]})
else:print('ambientCG download link not found; retained as candidate.',flush=True)
(ROOT/'00_admin/asset_manifest.json').write_text(json.dumps({'date':'2026-09-08','credit':'Powered by Poly Haven; ambientCG','assets':assets},ensure_ascii=False,indent=2),encoding='utf-8')
print('Asset manifest saved.',flush=True)
