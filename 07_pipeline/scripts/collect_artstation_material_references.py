"""读取公开 ArtStation 作品页中的展示图片地址；仅作材质参考，不取付费资源。"""
import requests
import re
import json
import html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'01_preproduction/references/material_studies'
OUT.mkdir(parents=True,exist_ok=True)
sources=[('painted_metal','https://andreariccardi.artstation.com/projects/QzmB2B'),
         ('paint_smart','https://tsvetelina-valkanova.artstation.com/projects/mN3JY'),
         ('rust_breakdown','https://www.artstation.com/artwork/WBYQZD'),
         ('cod_school_desk','https://www.artstation.com/artwork/1NleAK')]
records=[]
for name,url in sources:
    response=requests.get(url,timeout=30)
    # 只解析页面已公开的展示链接；遇到身份验证/错误页则记录状态并停止该来源。
    print(name,response.status_code,len(response.content),flush=True)
    if response.status_code!=200:continue
    raw=html.unescape(response.text).replace('\\/','/')
    links=sorted(set(re.findall(r'https://[^\s<>"\']*artstation[^\s<>"\']*\.(?:jpg|png|jpeg)(?:\?[^\s<>"\']*)?',raw)))
    links=[p for p in links if '/images/images/' in p]
    for i,p in enumerate(links):print(name,i,p,flush=True)
    records.append({'name':name,'page':url,'display_images':links})
(OUT/'discovered_pages.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
