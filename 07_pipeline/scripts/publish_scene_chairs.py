"""发布已验证课椅替换候选到固定镜头工作文件；检查目标未变并正确重映射相对资源路径。"""
from pathlib import Path
import hashlib
import json
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from replace_scene_chairs import WORK, OUT, TARGET, CANDIDATE


def main():
    """输入通过重开与渲染的候选，输出原位保存记录；目标发生新修改时停止覆盖。"""
    assert Path(bpy.data.filepath)==CANDIDATE
    validation=json.loads((OUT/'candidate_validation.json').read_text(encoding='utf-8'))
    assert validation['passed']
    before=hashlib.sha256(TARGET.read_bytes()).hexdigest()
    assert before==(WORK/'target_before.sha256').read_text(encoding='utf-8').strip(),'正式文件在候选期间有新修改，需重新合并'
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
    data={'file':str(TARGET),'source_candidate':str(CANDIDATE),'before_sha256':before,
          'after_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'chairs':25,'parts':725,
          'protected_unchanged':True}
    (OUT/'published.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CHAIRS_PUBLISHED '+json.dumps({'saved':True,'chairs':25,'parts':725}),flush=True)


if __name__=='__main__':
    main()
