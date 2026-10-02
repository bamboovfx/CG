"""从Poly Haven公开API获取CC0木材资产，记录许可、原始尺寸和文件哈希。

输入：明确选定的三个木材资产；输出：原始纹理与资产清单，供SD研究和制作。
不下载网站预览渲染，也不把参考素材冒充自行生成的纹理。
"""
from pathlib import Path
import json
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'02_assets/textures/external/polyhaven_wood_detail'
HEADERS={'User-Agent':'Mozilla/5.0 (Wood material study; Poly Haven public API)'}


def request_json(url):
    """输入公开API地址，返回解析后的资产文件信息。"""
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=30) as response: return json.load(response)


def fetch(job):
    """输入下载规格，保存原始文件并校验API给出的MD5，返回可追溯记录。"""
    asset,channel,resolution,fmt,record=job
    folder=DEST/asset; folder.mkdir(parents=True,exist_ok=True)
    path=folder/record['url'].rsplit('/',1)[-1]
    if not path.exists():
        req=urllib.request.Request(record['url'],headers=HEADERS)
        with urllib.request.urlopen(req,timeout=60) as response, path.open('wb') as target:
            while chunk:=response.read(1024*1024): target.write(chunk)
    digest=hashlib.md5(path.read_bytes()).hexdigest()
    assert digest==record['md5'],(asset,channel,'download checksum mismatch')
    with Image.open(path) as im: size=list(im.size)
    result={'asset':asset,'channel':channel,'resolution':resolution,'format':fmt,'url':record['url'],
        'path':str(path.relative_to(ROOT)),'pixels':size,'md5':digest,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'license':'CC0-1.0','license_url':'https://polyhaven.com/license','source_page':'https://polyhaven.com/a/'+asset}
    print('FETCHED '+asset+' '+channel+' '+resolution+' '+str(size),flush=True)
    return result


def main():
    """先取三份原始低分辨率色图做研究，再获取选定旧木材的原生8K细节。"""
    DEST.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for asset in ('wood_table_worn','wood_table_large','wood_table_001'):
        files=request_json('https://api.polyhaven.com/files/'+asset)
        (DEST/(asset+'_files.json')).write_text(json.dumps(files,indent=2),encoding='utf-8')
        jobs.append((asset,'Diffuse','1k','jpg',files['Diffuse']['1k']['jpg']))
        if asset=='wood_table_worn':
            for channel,fmt in [('Diffuse','jpg'),('Rough','jpg'),('nor_gl','png'),('Displacement','png')]:
                jobs.append((asset,channel,'8k',fmt,files[channel]['8k'][fmt]))
    with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,jobs))
    (DEST/'manifest.json').write_text(json.dumps({'sources':results,'use':'CC0 original production texture assets; reference study'},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__': main()
