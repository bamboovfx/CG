"""Audit a Tripo mesh in a separate background Blender process."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def mesh_bounds(objects):
    """Return world-space min/max bounds for input mesh objects."""
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


def inspect_mesh(path):
    """Import the input GLB and return geometry, UV, and material metadata."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects:
        raise ValueError("No mesh objects were imported")
    bounds = mesh_bounds(objects)
    return {
        "input": str(path),
        "blender_version": bpy.app.version_string,
        "objects": [
            {
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "edges": len(obj.data.edges),
                "faces": len(obj.data.polygons),
                "triangles": sum(max(len(poly.vertices) - 2, 0) for poly in obj.data.polygons),
                "uv_layers": [uv.name for uv in obj.data.uv_layers],
                "materials": [material.name if material else None for material in obj.data.materials],
            }
            for obj in objects
        ],
        "bounds": bounds,
        "dimensions": [bounds["maximum"][axis] - bounds["minimum"][axis] for axis in range(3)],
        "images": [
            {"name": image.name, "size": list(image.size), "source": image.source}
            for image in bpy.data.images
            if image.source == "FILE"
        ],
    }


def main():
    """Read Blender CLI arguments and write the mesh audit report."""
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    input_path, output_path = map(Path, arguments[:2])
    report = inspect_mesh(input_path)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("AUDIT_RESULT " + json.dumps({"objects": len(report["objects"]), "dimensions": report["dimensions"]}))


if __name__ == "__main__":
    main()
