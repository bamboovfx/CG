"""Audit a Tripo FBX in Blender without changing the source file.

Input: FBX path. Output: JSON path after `--` on the Blender command line.
"""

import bpy
import json
import sys
from collections import Counter
from mathutils import Vector
from pathlib import Path


def world_bounds(objects):
    """Return world-space bounds of all imported mesh objects."""
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = [min(c[index] for c in corners) for index in range(3)]
    high = [max(c[index] for c in corners) for index in range(3)]
    return {"minimum": low, "maximum": high, "size": [high[i] - low[i] for i in range(3)]}


def component_count(mesh):
    """Count vertex-connected pieces; input is a Blender mesh, output an integer."""
    parent = list(range(len(mesh.vertices)))

    def root(index):
        """Find the representative vertex index of one connected component."""
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in mesh.edges:
        a, b = edge.vertices
        ra, rb = root(a), root(b)
        parent[ra] = rb
    return len({root(index) for index in range(len(mesh.vertices))})


def audit_object(obj):
    """Summarize topology, UV and material slots of one imported mesh object."""
    mesh = obj.data
    poly_sizes = Counter(len(poly.vertices) for poly in mesh.polygons)
    edge_faces = Counter(edge_key for poly in mesh.polygons for edge_key in poly.edge_keys)
    uv = mesh.uv_layers.active
    uv_min = uv_max = None
    if uv:
        coords = [loop.uv for loop in uv.data]
        uv_min = [min(c[axis] for c in coords) for axis in range(2)]
        uv_max = [max(c[axis] for c in coords) for axis in range(2)]
    return {
        "name": obj.name,
        "vertices": len(mesh.vertices),
        "faces": len(mesh.polygons),
        "face_sizes": dict(poly_sizes),
        "components": component_count(mesh),
        "boundary_edges": sum(count == 1 for count in edge_faces.values()),
        "nonmanifold_edges": sum(count > 2 for count in edge_faces.values()),
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "uv_bounds": {"min": uv_min, "max": uv_max},
        "materials": [material.name if material else None for material in mesh.materials],
    }


def main():
    """Import the requested FBX and write a compact audit JSON report."""
    args = sys.argv[sys.argv.index("--") + 1 :]
    fbx_path, report_path = map(Path, args[:2])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    report = {
        "input": str(fbx_path),
        "blender_version": bpy.app.version_string,
        "bounds_m": world_bounds(objects),
        "objects": [audit_object(obj) for obj in objects],
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FBX_AUDIT=" + json.dumps(report))


main()
