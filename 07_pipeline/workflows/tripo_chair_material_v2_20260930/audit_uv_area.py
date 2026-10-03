"""Measure existing Tripo UV allocation before choosing the bake layout."""

import bpy
import json
from pathlib import Path


SOURCE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930/chair_material_v2_working.blend")


def area(points):
    """Return polygon area in normalized UV space using the shoelace formula."""
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points)))) * 0.5


def main():
    """Print occupied UV area and range for each chair mesh part."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    report = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.startswith("LP_part_"):
            continue
        uv = obj.data.uv_layers.active.data
        polygons = []
        coords = []
        for polygon in obj.data.polygons:
            points = [uv[loop].uv[:] for loop in polygon.loop_indices]
            polygons.append(area(points))
            coords.extend(points)
        report[obj.name] = {
            "uv_area": sum(polygons),
            "range": [min(p[0] for p in coords), min(p[1] for p in coords), max(p[0] for p in coords), max(p[1] for p in coords)],
        }
    print("UV_AREA=" + json.dumps(report))


main()
