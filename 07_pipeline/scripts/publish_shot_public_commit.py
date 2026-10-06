"""Prepare a public fast-forward commit without altering local-only tests or user deletions.

Use an alternate index; preserve the unpublished history in a local backup branch.
This script does not push, delete work files, bypass hooks or force-update remote refs.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '07_pipeline/cache/shot_external_links_20261006'
REVIEW = ROOT / '06_review/shot_external_links_20261006'
PRIVATE_PREFIXES = ('.scratch/sd-artstation-test/', '02_assets/materials/tlou_brick_type_a/',
                    '06_review/sd_artstation_test_20261006/')
PRIVATE_SCRIPTS = {'07_pipeline/scripts/render_sd_brick_test.py',
                   '07_pipeline/scripts/sd_artstation_brick_test.py',
                   '07_pipeline/scripts/verify_sd_brick_test.py'}


def git(args, env=None, data=None):
    """Input Git args/optional alternate index and stdin bytes; return successful UTF-8 stdout."""
    result = subprocess.run(['git', *args], cwd=ROOT, env=env, input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout.decode('utf-8').strip()


def is_private(path):
    """Input repository path; identify the user-designated local-only independent test."""
    return path.startswith(PRIVATE_PREFIXES) or path in PRIVATE_SCRIPTS


def filter_private_paragraphs(text):
    """Input shared doc text; omit only local-test paragraphs in the staged public copy."""
    parts = text.replace('\r\n', '\n').split('\n\n')
    return '\n\n'.join(part for part in parts if not (
        part.startswith('**') and any(token in part for token in
        ('sd_artstation_test_20261006', 'tlou_brick_type_a', 'SD测试仅本机'))))


def main():
    """Stage owned verified files in an alternate index, create backed-up public history and align index."""
    verification = json.loads((REVIEW / 'published_verification.json').read_text(encoding='utf-8'))
    assert verification['passed']
    shot = ROOT / '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
    with shot.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == verification['sha256']
    old_head = git(['rev-parse', 'HEAD'])
    upstream = git(['rev-parse', 'origin/main'])
    live = git(['ls-remote', 'origin', 'refs/heads/main']).split()[0]
    assert live == upstream, 'Remote changed; fetch and merge before publication.'
    assert not git(['diff', '--cached', '--name-only']), 'Preserve another task staged changes first.'
    env = {**os.environ, 'GIT_INDEX_FILE': str(CACHE / 'public.index')}
    git(['read-tree', old_head], env)
    manifest = json.loads((REVIEW / 'upload_manifest.json').read_text(encoding='utf-8'))
    owned = ['.gitignore', 'AGENTS.md', '00_admin/asset_manifest.json', '00_admin/current_state.md',
             'SESSION_HANDOFF.md', 'docs/cloud/README.md', 'docs/adr/002-external-geometry-local-shading.md',
             '.scratch/shot-external-links/spec.md', '.scratch/shot-external-links/issues/01-externalize.md',
             '07_pipeline/scripts/externalize_shot_assets.py', '07_pipeline/scripts/record_shot_external_dependencies.py',
             '07_pipeline/scripts/publish_shot_public_commit.py', 'scripts/check_cloud_assets.py']
    owned += [row['path'] for row in manifest['files']]
    owned += [p.relative_to(ROOT).as_posix() for p in REVIEW.iterdir() if p.suffix in {'.md', '.json'}]
    git(['add', '--', *sorted(set(owned))], env)
    staged = git(['ls-files'], env).splitlines()
    private = [path for path in staged if is_private(path)]
    if private:
        git(['update-index', '--force-remove', '--', *private], env)
    # Preserve the full private paragraphs on disk; only the public index copy is filtered.
    for path in ('00_admin/current_state.md', 'SESSION_HANDOFF.md'):
        current = (ROOT / path).read_text(encoding='utf-8')
        public = filter_private_paragraphs(current)
        oid = git(['hash-object', '-w', '--stdin'], data=public.encode('utf-8'))
        git(['update-index', '--cacheinfo', '100644', oid, path], env)
    tree = git(['write-tree'], env)
    assert not any(is_private(p) for p in git(['ls-tree', '-r', '--name-only', tree]).splitlines())
    message = ('Externalize classroom geometry and textures; retain editable shot shading\n\n'
               'Publish the verified current shot with external mesh data and exact external texture payloads. '
               'Keep existing material nodes, effective bindings, instances, camera and animation. '
               'Include pending verified desk publication. Keep independent local-only test files and '
               'the oversized unpublished scene versions outside public history.\n\n'
               'Validation: independent reopen; geometry/shader protection; 414 dependency hashes; '
               'same-frame CPU preview comparison.\n')
    public_commit = git(['commit-tree', tree, '-p', upstream], data=message.encode('utf-8'))
    backup = 'refs/heads/codex/backup-cg-before-links-20261006'
    existing = subprocess.run(['git', 'rev-parse', '--verify', backup], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert existing.returncode != 0, 'Backup ref exists; preserve it and choose a new name.'
    assert git(['rev-parse', 'HEAD']) == old_head and not git(['diff', '--cached', '--name-only'])
    git(['update-ref', backup, old_head, '0' * 40])
    git(['update-ref', 'refs/heads/main', public_commit, old_head])
    git(['read-tree', public_commit])  # Index only: all unrelated work files remain untouched.
    receipt = {'original_local_head': old_head, 'remote_base': upstream, 'public_commit': public_commit,
               'local_history_backup': backup, 'private_paths_excluded': len(private),
               'force_push': False, 'working_files_removed': False}
    (CACHE / 'public_preparation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
