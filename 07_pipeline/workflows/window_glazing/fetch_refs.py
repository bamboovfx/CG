"""下载公开厂商/施工参考，只供项目研究；记录来源、版权和哈希。"""
import urllib.request, hashlib, json
from pathlib import Path
out=Path('D:/00_projects/10_CG/Shot_Test/01_preproduction/references/window_glazing_20260928')
out.mkdir(parents=True,exist_ok=True)
sources={
 'installer_dismantled.jpg':'https://www.34al.com/images/construction/ss90-03.jpg',
 'installer_finished.jpg':'https://www.34al.com/images/construction/ss90-17.jpg',
 'installer_glass_seating.jpg':'https://www.34al.com/images/construction/ss90-04.jpg',
 'glazing_sections.pdf':'https://glass-wonderland.jp/cms/wp-content/themes/httpdocs/assets/pdf/total_s13-160.pdf',
 'gasket_section.jpg':'https://www-giya-man-com.imgix.net/images/624/c511a7a6-173b-4e74-a43b-c20d7bfa2eca-1728622076612.jpg',
 'gasket_on_glass.jpg':'https://www-giya-man-com.imgix.net/images/624/0e438e65-881e-44de-ac15-dbde6f324f99-1728622099378.jpg',
 'real_window.jpg':'https://www-giya-man-com.imgix.net/images/624/fc41a53d-eb35-44b3-bd11-a3acb73d7f24-1728621769016.jpg'}
rows=[]
for name,url in sources.items():
    try:
        data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
        (out/name).write_bytes(data)
        rows.append(dict(file=name,url=url,sha256=hashlib.sha256(data).hexdigest(),rights='原作者版权；本地研究，不授权再分发'))
    except Exception as e:rows.append(dict(file=name,url=url,error=str(e)))
(out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(rows,ensure_ascii=False))
