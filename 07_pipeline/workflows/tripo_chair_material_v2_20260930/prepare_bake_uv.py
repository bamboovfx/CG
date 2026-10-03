"""Repack the Tripo chair into separate wood and hardware UV texture sets."""

import bpy
import json
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
SOURCE = BASE / "chair_material_v2_working.blend"
OUTPUT = BASE / "chair_material_v2_uv.blend"
WOOD_PARTS = {"LP_part_02", "LP_part_09"}
PLAIN_PARTS = {"LP_part_00", "LP_part_03", "LP_part_06", "LP_part_07", "LP_part_10", "LP_part_11", "LP_part_12", "LP_part_14", "LP_part_15", "LP_part_17", "LP_part_18", "LP_part_19", "LP_part_20"}


def uv_area(points):
    """Return the absolute polygon area in normalized UV coordinates."""
    return abs(sum(points[index][0] * points[(index + 1) % len(points)][1] - points[(index + 1) % len(points)][0] * points[index][1] for index in range(len(points)))) * 0.5


def measure(objects):
    """Measure occupied UV area, bounds and selected face count for a set."""
    area = 0.0
    coords = []
    faces = 0
    for obj in objects:
        data = obj.data.uv_layers.active.data
        for polygon in obj.data.polygons:
            points = [data[index].uv[:] for index in polygon.loop_indices]
            area += uv_area(points)
            coords.extend(points)
            faces += 1
    return {
        "uv_area_sum": area,
        "bounds": [min(point[0] for point in coords), min(point[1] for point in coords), max(point[0] for point in coords), max(point[1] for point in coords)],
        "face_count": faces,
        "equivalent_square_pixels_at_4k": round((area ** 0.5) * 4096),
    }


def pack(objects):
    """Pack all islands from multiple objects into one 0–1 atlas with 16 px margin."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin=16.0 / 4096.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return measure(objects)


def smart_repack(objects):
    """Reproject fragmented hardware faces and pack them as one material set."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=16.0 / 4096.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return measure(objects)


def main():
    """Keep original UVs, pack two texture sets and save an editable UV stage."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    parts = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")]
    assert len(parts) == 26
    for obj in parts:
        uv = obj.data.uv_layers.new(name="UV_Material", do_init=True)
        obj.data.uv_layers.active = uv
        uv.active_render = True
    wood = [obj for obj in parts if obj.name in WOOD_PARTS]
    paint = [obj for obj in parts if obj.name not in WOOD_PARTS | PLAIN_PARTS]
    before = {"wood": measure(wood), "paint": measure(paint)}
    after = {"wood": pack(wood), "paint": smart_repack(paint)}
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    audit = {"source": str(SOURCE), "output": str(OUTPUT), "uv_name": "UV_Material", "original_uv_retained": True, "margin_px_at_4k": 16, "plain_material_parts_outside_bake": sorted(PLAIN_PARTS), "before": before, "after": after}
    (BASE / "uv_repack_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print("UV_REPACK_AUDIT=" + json.dumps(audit))


main()
