"""汇总四次小样数据及输入哈希；不将有限复测解释为稳定性能百分比。"""
import json,hashlib
from pathlib import Path
root=Path('D:/00_projects/10_CG/Shot_Test');out=root/'06_review/pipeline_review_20260929'
rows={n:json.loads((out/(n+'.json')).read_text()) for n in ['linked_test','local_test','linked_repeat','local_repeat']}
files=['02_assets/library/classroom_assets.blend','02_assets/work/classroom_environment.blend','07_pipeline/cache/pipeline_review_20260929/live_linked.blend','07_pipeline/cache/pipeline_review_20260929/local_candidate.blend']
summary={'tests':{n:{'render_seconds':r['render_wall_seconds'],'private_MiB_before_render':r['memory']['private_MiB'],'private_MiB_after_render':r['after_render_memory']['private_MiB'],'file_MiB':r['file_bytes']/1048576} for n,r in rows.items()},'input_hashes':{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},'scope':'Blender5.1.2 OptiX 1076帧 640x270 16samples；保留实例；包含场景同步的渲染调用；非严格性能基准，未测播放FPS及GPU显存','conclusion':'载入数据结构无减少；复测用时与私有提交内存接近，未观察到分文件明显性能优势。首轮受缓存/系统负载影响，不报告稳定提速百分比。'}
(out/'measurements.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
p=out/'proposal.md';s=p.read_text(encoding='utf8')
s=s.replace('单次A/B不能当成稳定速度百分比','两组有限A/B不能当成稳定速度百分比')
table='\n### 实测记录\n\n| 指标 | 外部链接 | 本地共享数据 |\n|---|---:|---:|\n'
for label,key,div in [('主文件 MiB','file_MiB',1),('复测渲染调用 秒','render_seconds',1),('复测渲染后私有提交内存 GiB（非显存）','private_MiB_after_render',1024)]:
    table+=f"| {label} | {summary['tests']['linked_repeat'][key]/div:.2f} | {summary['tests']['local_repeat'][key]/div:.2f} |\n"
table+='\n首轮链接79.17秒、本地37.80秒；复测27.14/26.77秒，显示首次缓存与负载干扰很大。因此仅得出“本次未观察到明显分文件性能优势”，不宣称固定提速比。详细值与输入哈希见[实测JSON](measurements.json)。\n'
s=s.replace('## 推荐的日常使用方式',table+'\n## 推荐的日常使用方式');p.write_text(s,encoding='utf8')
print(json.dumps(summary['tests'],ensure_ascii=False))
