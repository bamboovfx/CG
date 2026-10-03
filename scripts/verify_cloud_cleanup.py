"""汇总清理前后检查，禁止以文件计数相等代替依赖和哈希保护。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / '06_review/cloud_assets_20261003'


def external_resources(row):
    """输入单工程检查；返回真实外部资源集合，忽略仅作为标签的打包资源来源路径。"""
    return {(r['kind'], r['name'], Path(r['absolute']).resolve().as_posix().casefold(), r['exists'])
            for r in row['resources'] if not r['packed']}


def main():
    """读取前后审计及迁移/路径验证；输出可核对的验证结果与中文报告。"""
    before = json.loads((REVIEW / 'dependencies_before.json').read_text(encoding='utf-8'))
    after = json.loads((REVIEW / 'dependencies_after.json').read_text(encoding='utf-8'))
    moves = json.loads((REVIEW / 'moved.json').read_text(encoding='utf-8-sig'))
    deleted = json.loads((REVIEW / 'deleted.json').read_text(encoding='utf-8-sig'))
    mapping = {r['source']: r['destination'] for r in moves}
    portable = json.loads((REVIEW / 'drop_sq010_sh010_shot_portable.json').read_text(encoding='utf-8'))
    checks = []
    assert len(before) == len(after) == 11
    for old, new in zip(before, after):
        assert new['file'] == mapping.get(old['file'], old['file'])
        expected_hash = portable['after_sha256'] if old['file'] == portable['file'] else old['sha256']
        passed = (new['sha256'] == expected_hash and new['unchanged']
                  and external_resources(old) == external_resources(new)
                  and all(old[k] == new[k] for k in ('objects', 'meshes', 'materials', 'actions', 'scenes', 'caches')))
        checks.append(dict(file=new['file'], passed=passed,
                           existing_missing=sum(not r['packed'] and not r['exists'] for r in new['resources'])))
    assert all(r['passed'] for r in checks), checks
    assert portable['content_preserved'] and portable['semantic_before'] == portable['semantic_after']
    assert all(not (ROOT / r['path']).exists() for r in deleted)
    assert all((ROOT / r['destination']).is_file() for r in moves)
    assert not any(p.is_file() for p in (ROOT / '07_pipeline/cache').rglob('*'))
    result = dict(passed=True, reopened_files=checks, deleted_files=len(deleted),
                  deleted_bytes=sum(r['bytes'] for r in deleted), retained_moves=len(moves),
                  portable_scene_content_unchanged=True, new_missing_resources=0,
                  scene_sha256=portable['after_sha256'])
    (REVIEW / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    report = f'''# 云端资产整理 · 2026-10-03

范围为 `D:/00_projects/10_CG/Shot_Test`，远程仍是公开 `bamboovfx/CG`；相邻项目未清理。用户授权清除缓存及旧资产版本、保留已验证流程，并优先上传当前镜头使用的资产。

## 清理与保留

实际删除 **{len(deleted)}个文件，{result['deleted_bytes']:,}字节（{result['deleted_bytes']/1024**3:.2f}GiB）**。包含课椅分阶段旧版本、旧镜头候选/恢复副本、重复快照、测试输出/日志、自动备份和字节码。逐文件记录见 `deleted.json`，原计划见 `cleanup_plan.json`；删除记录不是可恢复备份。

迁移 **{len(moves)}项** 并验证SHA256。最新课椅为 `02_assets/work/school_chair.blend`；最新v4课桌为 `02_assets/work/school_desk_parts.blend`，原始FBX在 `02_assets/authoring/school_desk/`，共享材质源为 `02_assets/work/approved_material_library.blend`。后二者未并入镜头，保留本机不上传。保留最新SP自动保存作为制作源，并保存高模/烘焙输入；它们不属于运行缓存，保留在 `02_assets/authoring/school_chair/`，本轮也不上传。

原生SD源、正式贴图、旧建筑/道具/库/布料制作源、视频和评审图继续保留。未使用资产只排除上传，未据此从本机删除。可复现阶段脚本迁至 `07_pipeline/workflows/`；它们仍是历史配方，运行前须重建已清理的阶段输入。原任务/规格和制作状态继续保留，看板重新检查。

## 镜头与依赖验证

清理前后均独立后台重开11份保留工程；未移动文件与迁移文件的SHA256得到保护，真实外部依赖集合相同，**新增缺失0**。布料内嵌烘焙缓存保留，没有把保存在工程中的可重算制作数据当作临时目录清除。

正式镜头规范化{len(portable['changes'])}条项目内外部路径，统一相对路径及斜杠，按固定工作路径保存。保存重开前后的几何/UV/法线、对象变换/实例、材质节点/打包图像、集合关系、动作、相机/世界/帧范围和场景摘要完全相同；摘要见 `drop_sq010_sh010_shot_portable.json`。当前文件SHA256为 `{portable['after_sha256']}`。

## 上传配置与去重

`.gitignore` 改为文档/工具加精确资产白名单，`.gitattributes` 为工程和图片启用 Git LFS，已安装本仓库的LFS钩子，uGit直接使用同一规则。`upload_manifest.json` 记录入选文件尺寸、SHA256、原因和未入选本机资产；`scripts/check_cloud_assets.py --hash` 可检查真实LFS文件。云端安装脚本先拉取LFS，再验收Blender运行环境。

相同像素/字节的贴图有时是不同节点所需的通道或不同资产路径，不能只因哈希相同删掉依赖；LFS按SHA256共享一个存储对象，避免重复上传相同内容。旧版本文件则已按上方记录实际删除。

## 限制与历史证据

镜头在整理前已有5张Houdini opdef测试人物贴图缺失，并依赖未上传的Windows Arial Narrow系统字体；本轮没有替换它们或改变画面。镜头仍为1001–1100/24fps，cam_sh010_main，140帧目标未完成。140帧候选工程和旧FFmpeg缓存运行时在本轮开始前已不在磁盘；视频、制作配方和历史报告仍在。

本轮清缓存时连同缓存内3份9月29日迁移验收JSON一起删除。迁移报告的结构/发布哈希摘要和原画面对照保留；任务证据入口已修正。木椅旧分阶段模型由最新整合源取代，任务中保留阶段报告与最新源入口。此处明确保留历史事实，不将本轮检查冒充当时的细项验收。

这轮是本机清理、依赖检查和仓库上传；不等于已发布云端环境的正式镜头重开/渲染或用户视觉验收。公开仓库继续排除原片、参考网站照片、系统字体、缓存、日志与凭据。
'''
    (REVIEW / 'report.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
