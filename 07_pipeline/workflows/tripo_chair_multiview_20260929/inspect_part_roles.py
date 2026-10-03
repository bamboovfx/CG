"""Create a labeled material-ID render for the separated Tripo chair parts."""

import bpy
import colorsys
import json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")


def main():
    """Render each part as a distinct color and report its projected location."""
    bpy.ops.wm.open_mainfile(filepath=str(BASE / "tripo_chair_pbr_candidate.blend"))
    scene = bpy.context.scene
    parts = sorted((obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")), key=lambda obj: obj.name)
    report = []
    for index, obj in enumerate(parts):
        color = colorsys.hsv_to_rgb(index / len(parts), 0.75, 0.9)
        material = bpy.data.materials.new(f"ID {obj.name}")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*color, 1)
        emission.inputs["Strength"].default_value = 1.0
        material.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
        obj.data.materials.clear()
        obj.data.materials.append(material)
        center = obj.matrix_world @ Vector((0, 0, 0))
        screen = world_to_camera_view(scene, scene.camera, center)
        report.append({"name": obj.name, "center": list(center), "dimensions": list(obj.dimensions), "screen": [screen.x, screen.y], "rgb": color})
    scene.render.filepath = str(BASE / "candidate_part_ids.png")
    scene.cycles.samples = 8
    bpy.ops.render.render(write_still=True)
    (BASE / "candidate_part_ids.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for item in report:
        print("PART_ID=" + json.dumps(item))


main()
