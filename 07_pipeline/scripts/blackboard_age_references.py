"""保存公开厂商参考图及来源；仅作观察，不把参考像素带进新材质。"""
from pathlib import Path
from urllib.request import Request, urlopen
import concurrent.futures, hashlib, json

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'01_preproduction/references/blackboard_age_20260919'
OUT.mkdir(parents=True,exist_ok=True)
sources=[
 {'title':'青井黒板：烤漆钢板与玻璃质珐琅的工艺区别','url':'https://www.aoikokuban.co.jp/support01/','role':'工艺事实；选择烤漆钢板作为本次制作设定。'},
 {'title':'永和：表面材样品','url':'https://eiwa-k.jp/product_category/surface_material/','role':'新板颜色、钢板烤漆与珐琅耐久性差异。'},
 {'title':'長野特殊黒板：磨损、擦拭与白化','url':'https://www.nagano-kokuban.com/faq.php','role':'微齿磨平产生反光；粉笔嵌入细沟产生残留，实物前后照片。'},
 {'title':'馬印：板材与维护问答','url':'https://www.uma-jirushi.co.jp/faq','role':'珐琅与钢板不同，板擦清洁影响残留。'},
 {'title':'東黒：钢板书写面磨损说明','url':'https://www.tokoku.co.jp/images/catalog.pdf','role':'反复书写、擦除逐渐磨损涂层，不能把所有老化都做成粗糙增大。'},
 {'title':'Resene：涂膜褪色与粉化','url':'https://www.resene.co.nz/homeown/problem-solver/caring-for-your-paint-finish.htm','role':'一般涂料老化机理；并非本片黑板的检测报告。日晒分布与强度是艺术设定。'},
 {'title':'Michael Jenkins：Abandoned Classroom','url':'https://michaeljayjenkins.artstation.com/projects/dO4ALJ','role':'CG 制作参考：独立黑板 alpha、材质分层。废弃程度不套用到当前教室。'},
 {'title':'Michael Jenkins：制作 breakdown','url':'https://www.artstation.com/artwork/BmvzRr','role':'补充环境制作流程参考。'},
 {'title':'Anderson Barboza：School blackboard','url':'https://www.artstation.com/marketplace/p/y1aB2/school-blackboard','role':'CG 资产参考，未购买或下载付费资产。'},
 {'title':'日学：木框黑板规格','url':'https://www.nichigaku.co.jp/digicata/kyougaku.pdf','role':'木框并不能单独证明板面工艺，需将制造假设与原片事实分开。'}]
images=[('whitening','hakuka1.jpg'),('before_cleaning','sirobfo.jpg'),('after_cleaning','siroaft.jpg'),('ground_coating','mntogi.jpg')]

def download(item):
    """输入本地标识及已公开图片名；返回下载状态和哈希，不改变图片内容。"""
    name,filename=item
    url='https://www.nagano-kokuban.com/images/'+filename
    try:
        data=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
        path=OUT/(name+'.jpg');path.write_bytes(data)
        return {'title':name,'url':url,'path':path.name,'sha256':hashlib.sha256(data).hexdigest(),
                'rights':'厂商版权参考，仅研究；不用于纹理像素。'}
    except Exception as error:
        return {'title':name,'url':url,'error':str(error)}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    photos=list(pool.map(download,images))
(OUT/'sources.json').write_text(json.dumps({'sources':sources,'photos':photos},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(photos,ensure_ascii=False),flush=True)
