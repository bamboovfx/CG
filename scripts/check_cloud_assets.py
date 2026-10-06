"""核对 Git LFS 资产是否完整下载；明确列出已知镜头资源缺口。"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = {'.blend', '.fbx', '.glb', '.spp', '.sbsar', '.png', '.jpg', '.jpeg', '.webp', '.exr', '.hdr'}


def main():
    """接受可选 --hash；核对二进制尺寸/指针，必要时验证 SHA256；缺失即退出非零。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hash', action='store_true', help='分块验证全部入选二进制的 SHA256')
    args = parser.parse_args()
    manifest_path = ROOT / '06_review/shot_external_links_20261006/upload_manifest.json'
    if not manifest_path.exists():
        manifest_path = ROOT / '06_review/cloud_assets_20261003/upload_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    errors = []
    count = 0
    for row in manifest['files']:
        path = ROOT / row['path']
        if path.suffix not in BINARY:
            continue
        count += 1
        if not path.is_file():
            errors.append(f"缺失: {row['path']}")
            continue
        with path.open('rb') as stream:
            prefix = stream.read(128)
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
            errors.append(f"仍是 LFS 指针，请先 git lfs pull: {row['path']}")
        elif path.stat().st_size != row['bytes']:
            errors.append(f"尺寸不一致: {row['path']}")
        elif args.hash:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(block)
            if digest.hexdigest() != row['sha256']:
                errors.append(f"SHA256 不一致: {row['path']}")
    print(f'Cloud asset binaries checked: {count}; errors: {len(errors)}', flush=True)
    for message in errors:
        print(message, flush=True)
    print('既有视觉限制：5张Houdini opdef人物贴图、黑板Abrasion及Arial Narrow字体缺失。', flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
