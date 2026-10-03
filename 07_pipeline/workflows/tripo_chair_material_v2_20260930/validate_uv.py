"""Check the repacked UVs and render a directional checker preview."""

import bpy
import json
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
SOURCE = BASE / "chair_material_v2_uv.blend"
WOOD_PARTS = {"LP_part_02", "LP_part_09"}
PLAIN_PARTS = {"LP_part_00", "LP_part_03", "LP_part_06", "LP_part_07", "LP_part_10", "LP_part_11", "LP_part_12", "LP_part_14", "LP_part_15", "LP_part_17", "LP_part_18", "LP_part_19", "LP_part_20"}


def triangles(objects):
    """Return UV triangles with face identity for a separate texture set."""
    result = []
    for obj in objects:
        uv = obj.data.uv_layers.active.data
        for polygon in obj.data.polygons:
            points = [tuple(uv[index].uv) for index in polygon.loop_indices]
            for index in range(1, len(points) - 1):
                tri = (points[0], points[index], points[index + 1])
                bounds = (min(point[0] for point in tri), min(point[1] for point in tri), max(point[0] for point in tri), max(point[1] for point in tri))
                result.append((obj.name, polygon.index, tri, bounds))
    return result


def intersects(first, second):
    """Use the 2D separating-axis test to reject edge-only triangle contact."""
    for triangle in (first, second):
        for index in range(3):
            start = triangle[index]
            end = triangle[(index + 1) % 3]
            axis = (start[1] - end[1], end[0] - start[0])
            a = [point[0] * axis[0] + point[1] * axis[1] for point in first]
            b = [point[0] * axis[0] + point[1] * axis[1] for point in second]
            if min(max(a), max(b)) - max(min(a), min(b)) <= 1e-8:
                return False
    return True


def overlap_count(objects):
    """Count overlapping UV triangle pairs with a grid-assisted exact test."""
    uv_tris = triangles(objects)
    cells = {}
    resolution = 128
    for index, item in enumerate(uv_tris):
        low_x, low_y, high_x, high_y = item[3]
        for x in range(max(0, int(low_x * resolution)), min(resolution - 1, int(high_x * resolution)) + 1):
            for y in range(max(0, int(low_y * resolution)), min(resolution - 1, int(high_y * resolution)) + 1):
                cells.setdefault((x, y), []).append(index)
    checked = set()
    overlapping = []
    for members in cells.values():
        for left_index in range(len(members)):
            for right_index in range(left_index + 1, len(members)):
                first = members[left_index]
                second = members[right_index]
                key = (min(first, second), max(first, second))
                if key in checked:
                    continue
                checked.add(key)
                a = uv_tris[first]
                b = uv_tris[second]
                if a[:2] != b[:2] and intersects(a[2], b[2]):
                    overlapping.append([a[0], a[1], b[0], b[1]])
    return {"pairs": len(overlapping), "examples": overlapping[:10], "uv_triangles": len(uv_tris)}


def checker_material():
    """Build a 1K color grid using the new UV map for visual stretch inspection."""
    grid = bpy.data.images.new("UV_Material checker", width=1024, height=1024, alpha=False)
    grid.generated_type = "COLOR_GRID"
    material = bpy.data.materials.new("UV_Material checker")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    uv = material.node_tree.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UV_Material"
    image = material.node_tree.nodes.new("ShaderNodeTexImage")
    image.image = grid
    material.node_tree.links.new(uv.outputs["UV"], image.inputs["Vector"])
    material.node_tree.links.new(image.outputs["Color"], shader.inputs["Base Color"])
    return material


def main():
    """Report Blender's overlap selection and write a close UV grid render."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    parts = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")]
    wood = [obj for obj in parts if obj.name in WOOD_PARTS]
    paint = [obj for obj in parts if obj.name not in WOOD_PARTS | PLAIN_PARTS]
    result = {"wood": overlap_count(wood), "paint": overlap_count(paint)}
    checker = checker_material()
    for obj in parts:
        obj.data.materials.clear()
        obj.data.materials.append(checker)
    scene = bpy.context.scene
    scene.render.filepath = str(BASE / "uv_checker_detail.png")
    scene.cycles.samples = 32
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.camera.location.z += 0.18
    scene.camera.data.ortho_scale = 0.72
    bpy.ops.render.render(write_still=True)
    (BASE / "uv_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("UV_VALIDATION=" + json.dumps(result))


main()
