"""将迁移前带链接的工程保存到评审目录，并重映射其相对库路径。"""
from pathlib import Path

import bpy


ROOT = Path("D:/00_projects/10_CG/Shot_Test")
TARGET = ROOT / "06_review/classroom_pipeline_migration_20260929/source_before.blend"
assert Path(bpy.data.filepath).name == "source_before.blend"
assert len(bpy.data.libraries) == 2
assert all(Path(bpy.path.abspath(lib.filepath)).exists() for lib in bpy.data.libraries)

# 不在正式镜头目录中产生额外版本；评审目录本身是恢复档案。
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), relative_remap=True)
print({"backup": str(TARGET), "libraries": [lib.filepath for lib in bpy.data.libraries]})
