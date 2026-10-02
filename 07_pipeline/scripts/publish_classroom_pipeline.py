"""核对原文件哈希后，将已验证的教室候选发布到固定镜头路径。"""
import hashlib
import json
from pathlib import Path

import bpy


ROOT = Path("D:/00_projects/10_CG/Shot_Test")
CACHE = ROOT / "07_pipeline/cache/classroom_pipeline_migration_20260929"
TARGET = ROOT / "03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend"
record = json.loads((CACHE / "candidate.json").read_text(encoding="utf8"))
check = json.loads((CACHE / "validation.json").read_text(encoding="utf8"))

# 在最后一刻核对正式文件，避免覆盖用户刚刚保存的新工作。
actual_hash = hashlib.sha256(TARGET.read_bytes()).hexdigest()
assert actual_hash == record["source_hash"], "正式镜头已更新，停止发布"
assert check["passed"] is True
assert Path(bpy.data.filepath).resolve() == (CACHE / "candidate.blend").resolve()
scene = bpy.context.scene
assert scene.name == "sq010_sh010" and scene.frame_current == 1076
assert scene.render.fps == 24 and [scene.frame_start, scene.frame_end] == [1001, 1100]
assert not list(bpy.data.libraries)
assert "Unique wiped writing surface" in scene.objects
assert bpy.data.collections["LOOKDEV / material selectors"] in scene.collection.children[:]

# 已在cache保存完整迁移前工程，因此不额外生成正式目录的.blend1。
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), relative_remap=True)
published_hash = hashlib.sha256(TARGET.read_bytes()).hexdigest()
(CACHE / "published.json").write_text(
    json.dumps(
        {
            "source_hash": actual_hash,
            "published_hash": published_hash,
            "target": str(TARGET),
            "backup": str(CACHE / "source_before.blend"),
            "visual_comparison": str(ROOT / "06_review/classroom_pipeline_migration_20260929"),
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf8",
)
print(json.dumps({"published_hash": published_hash, "target": str(TARGET)}))
