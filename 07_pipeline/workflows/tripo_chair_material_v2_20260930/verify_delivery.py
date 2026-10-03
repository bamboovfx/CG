"""Verify the delivered Blender chair and its baked PBR image dependencies."""

import bpy
import hashlib
import json
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
AUDIT = json.loads((BASE / "bake_audit.json").read_text(encoding="utf-8"))
bpy.ops.wm.open_mainfile(filepath=str(BASE / "chair_material_v2_baked.blend"))
parts = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")]
results = {"mesh_parts": len(parts), "all_triangles": all(len(face.vertices) == 3 for obj in parts for face in obj.data.polygons), "all_uv_material": all("UV_Material" in obj.data.uv_layers for obj in parts), "sets": {}}


def sha256(path):
    """Return the SHA256 digest for a saved texture file."""
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Check all five channels independently in each UV texture set.
for name, paths in AUDIT["texture_sets"].items():
    material = bpy.data.materials[f"Baked {name} PBR"]
    images = {node.get("role"): node.image for node in material.node_tree.nodes if node.type == "TEX_IMAGE"}
    checks = {}
    for channel, data in paths.items():
        image = images[channel]
        checks[channel] = {
            "size": list(image.size),
            "packed": bool(image.packed_file),
            "colorspace": image.colorspace_settings.name,
            "hash_matches": sha256(data["path"]) == data["sha256"],
        }
    results["sets"][name] = checks

results["pass"] = (
    results["mesh_parts"] == 26
    and results["all_triangles"]
    and results["all_uv_material"]
    and all(
        check["size"] == [4096, 4096]
        and check["packed"]
        and check["hash_matches"]
        and check["colorspace"] == ("sRGB" if channel == "BaseColor" else "Non-Color")
        for texture_set in results["sets"].values()
        for channel, check in texture_set.items()
    )
)
(BASE / "delivery_validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results), flush=True)
assert results["pass"]
