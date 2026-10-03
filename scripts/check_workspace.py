"""静态核对同步脚本，并在独立 Blender 后台验证执行环境。"""

import argparse
import ast
from pathlib import Path
import subprocess
import sys


def main() -> None:
    """接受 Blender 可执行路径；检查文档与语法，报告缺失正式资产，运行独立烟雾验收。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for name in ("AGENTS.md", "SESSION_HANDOFF.md", "CONTEXT.md", "00_admin/current_state.md",
                 ".scratch/sh010-test/spec.md", "docs/cloud/README.md"):
        if not (root / name).is_file():
            raise FileNotFoundError(name)
    # 只解析受版本控制的脚本，避免本机缓存/参考文件与云端检查范围不同。
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", "*.py"], cwd=root).split(b"\0")
    for raw in filter(None, tracked):
        path = root / raw.decode("utf-8")
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    print(f"Python syntax checked: {sum(bool(path) for path in tracked)}", flush=True)
    for name in ("03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend",
                 "02_assets/work/school_chair.blend"):
        print(f"Formal asset {'present locally' if (root / name).is_file() else 'not included'}: {name}", flush=True)
    # 先区分完整资产与 LFS 指针；默认烟雾场景通过不能替代正式镜头依赖检查。
    if (root / '06_review/cloud_assets_20261003/upload_manifest.json').is_file():
        subprocess.run([sys.executable, str(root / 'scripts/check_cloud_assets.py')],
                       cwd=root, check=True)
    subprocess.run([args.blender, "--background", "--factory-startup", "--python-exit-code", "1",
                    "--python", str(root / "scripts/blender_smoke.py")], cwd=root, check=True)


if __name__ == "__main__":
    main()
