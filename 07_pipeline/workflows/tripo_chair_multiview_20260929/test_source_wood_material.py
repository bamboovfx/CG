"""Compare the source chair wood shader on the Tripo reconstruction."""

import bpy
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")
SOURCE = Path("D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_props.blend")
MATERIAL_NAME = "Wood / 01 School board / chair / Surface / Desk family lightly worn wood"


def main():
    """Append only the source wood material, fix its images and render a comparison."""
    bpy.ops.wm.open_mainfile(filepath=str(BASE / "tripo_chair_reference_mat_candidate.blend"))
    with bpy.data.libraries.load(str(SOURCE), link=False) as (source, target):
        target.materials = [MATERIAL_NAME]
    wood = bpy.data.materials[MATERIAL_NAME]
    # Rebase appended relative paths to the source asset folder before packing.
    for node in wood.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image and node.image.filepath.startswith("//"):
            relative = node.image.filepath[2:].replace("\\", "/")
            marker = "textures/"
            assert marker in relative, relative
            node.image.filepath = str(SOURCE.parent.parent / marker / relative.split(marker, 1)[1])
            node.image.reload()
            node.image.pack()
    for name in ("LP_part_02", "LP_part_09"):
        obj = bpy.data.objects[name]
        obj.data.materials.clear()
        obj.data.materials.append(wood)
    scene = bpy.context.scene
    scene.render.filepath = str(BASE / "source_wood_test.png")
    scene.cycles.samples = 96
    bpy.ops.render.render(write_still=True)
    print("SOURCE_WOOD_TEST=" + str(BASE / "source_wood_test.png"))


main()
