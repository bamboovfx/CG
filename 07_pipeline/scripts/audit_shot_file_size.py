"""Read the current shot without saving; inventory embedded payloads and base meshes."""
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
SHOT = ROOT / '03_shots/sq010/sh010/work/drop_sq010_sh010_shot.blend'
OUT = ROOT / '06_review/git_push_check_20261006/size_audit.json'


def digest(path):
    """Input file path; return its SHA256 with bounded memory."""
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def inspect_images():
    """Read image payloads one at a time; return sizes, hashes and PNG headers."""
    records = []
    for image in bpy.data.images:
        payloads = []
        for item in image.packed_files:
            packed = item.packed_file
            data = packed.data
            header = data[:26]
            png = header.startswith(b'\x89PNG\r\n\x1a\n') and len(header) >= 26
            payloads.append(dict(bytes=packed.size, sha256=hashlib.sha256(data).hexdigest(),
                                 width=struct.unpack('>I', header[16:20])[0] if png else None,
                                 height=struct.unpack('>I', header[20:24])[0] if png else None,
                                 bit_depth=header[24] if png else None))
            del data
        records.append(dict(name=image.name, path=image.filepath, users=image.users,
                            fake_user=image.use_fake_user, source=image.source,
                            packed_bytes=sum(p['bytes'] for p in payloads), payloads=payloads))
    return sorted(records, key=lambda item: item['packed_bytes'], reverse=True)


def main():
    """Open disk shot read-only, write audit JSON, assert source hash remains unchanged."""
    before = digest(SHOT)
    bpy.ops.wm.open_mainfile(filepath=str(SHOT), load_ui=False)
    images = inspect_images()
    by_hash = defaultdict(list)
    for image in images:
        for payload in image['payloads']:
            by_hash[payload['sha256']].append(dict(name=image['name'], bytes=payload['bytes']))
    duplicates = [dict(sha256=key, copies=values, redundant_bytes=sum(v['bytes'] for v in values[1:]))
                  for key, values in by_hash.items() if len(values) > 1]
    meshes = [dict(name=mesh.name, users=mesh.users, vertices=len(mesh.vertices),
                   edges=len(mesh.edges), polygons=len(mesh.polygons), loops=len(mesh.loops),
                   shape_keys=len(mesh.shape_keys.key_blocks) if mesh.shape_keys else 0)
              for mesh in bpy.data.meshes]
    meshes.sort(key=lambda item: item['vertices'], reverse=True)
    result = dict(file=str(SHOT), file_bytes=SHOT.stat().st_size, sha256=before,
                  source_unchanged=digest(SHOT) == before,
                  images=images, packed_image_bytes=sum(i['packed_bytes'] for i in images),
                  duplicate_payloads=duplicates,
                  redundant_packed_bytes=sum(i['redundant_bytes'] for i in duplicates),
                  meshes=meshes, vertices=sum(m['vertices'] for m in meshes),
                  objects=len(bpy.data.objects), materials=len(bpy.data.materials),
                  libraries=[l.filepath for l in bpy.data.libraries],
                  scenes=[s.name for s in bpy.data.scenes], actions=len(bpy.data.actions))
    assert result['source_unchanged'], 'Source changed during audit; re-read before drawing conclusions.'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('SIZE_AUDIT', json.dumps({k: result[k] for k in ('file_bytes', 'packed_image_bytes',
          'redundant_packed_bytes', 'vertices', 'objects', 'source_unchanged')}), flush=True)


if __name__ == '__main__':
    main()
