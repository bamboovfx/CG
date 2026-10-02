"""独立重开新版胶脚表现，复用分层检查并确认工艺签名仍等于修改前。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_chair_foot_caps_materials as verifier
from chair_foot_caps_visibility import OUT
from chair_foot_caps_blender import PROCESS
from tripo_wood_appearance_blender import process_signature


def main():
    """输入已保存实时文件，输出依赖／保护检查与表现修改前后的工艺一致性。"""
    verifier.OUT=OUT
    verifier.main()
    audit=json.loads((OUT/'reopen_validation.json').read_text(encoding='utf-8'))
    applied=json.loads((OUT/'applied.json').read_text(encoding='utf-8'))
    audit['checks']['original_factory_unchanged']=process_signature(bpy.data.node_groups[PROCESS])==applied['process_signature']
    audit['passed']=all(audit['checks'].values())
    (OUT/'reopen_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    assert audit['passed']
    print('FOOT_CAP_VISIBILITY_REOPEN '+json.dumps({'passed':True,'checks':len(audit['checks'])}),flush=True)


if __name__=='__main__':
    main()
