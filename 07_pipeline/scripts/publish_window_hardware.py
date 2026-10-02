"""候选验证通过且源文件未被用户再次保存时，发布到固定建筑源；保留相对引用。"""
import bpy
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/00_projects/10_CG/Shot_Test')
source=ROOT/'02_assets/work/classroom_environment.blend'
review=ROOT/'06_review/window_hardware_correction'
validation=json.loads((review/'reopened_candidate.json').read_text(encoding='utf-8'))
assert validation['passed']
assert hashlib.sha256(source.read_bytes()).hexdigest()=='5aa422f3f595c3f3c4716797e7e2c76b66c99a98ee17e7315a2b7551aecf8946', 'Source changed; merge required'
assert bpy.data.filepath.replace('\\','/').endswith('/window_hardware_correction_20260927/candidate.blend')
# 已有本轮恢复副本，避免额外产生正式文件.blend1版本。
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(source),relative_remap=True,check_existing=False)
report=json.loads((review/'candidate_validation.json').read_text(encoding='utf-8'))
report.update(published_file=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              publish_note='建筑源窗口已关闭且文件哈希未变；发布经过验证的候选，保存时重映射相对依赖。')
(review/'published_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source':str(source),'sha256':report['sha256']}))
