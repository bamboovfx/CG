"""Connect the Painter pilot texture set to the editable chair candidate.

Inputs: UV candidate .blend and seven 2K Painter PNGs.
Outputs: separate PBR candidate .blend, material preview and material audit.
The source shot and UV candidate are left intact.
"""

import bpy
import json
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")
TEXTURES = BASE / "textures"
INPUT = BASE / "tripo_chair_blender_candidate.blend"
OUTPUT = BASE / "tripo_chair_pbr_candidate.blend"


def add_image(nodes, name, filename, color_space):
    """Load and pack one exported Painter map, then return its image node."""
    image = bpy.data.images.load(str(TEXTURES / filename), check_existing=False)
    image.colorspace_settings.name = color_space
    image.pack()
    node = nodes.new("ShaderNodeTexImage")
    # Keep Blender's default visible node name; store script lookup metadata internally.
    node["role"] = name
    node.image = image
    return node


def main():
    """Build the PBR graph, assign it to low-poly parts and render a preview."""
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    scene = bpy.context.scene
    parts = [obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")]
    assert len(parts) == 26, f"Expected 26 candidate parts, found {len(parts)}"

    material = bpy.data.materials.new("SP classroom chair PBR pilot")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    color = add_image(nodes, "Base Color / sRGB", "QA clay_Base_color.png", "sRGB")
    metal = add_image(nodes, "Metallic / linear", "QA clay_Base_metalness.png", "Non-Color")
    rough = add_image(nodes, "Roughness / linear", "QA clay_Specular_roughness.png", "Non-Color")
    normal_image = add_image(nodes, "Normal OpenGL / linear", "QA clay_Normal_OpenGL.png", "Non-Color")
    ao = add_image(nodes, "AO / linear", "QA clay_Mixed_AO.png", "Non-Color")
    # Store the height export in the Blender file for inspection; do not displace the low-poly mesh.
    height = add_image(nodes, "Height / archived", "QA clay_Height.png", "Non-Color")
    height.mute = True

    # Keep AO as a separate packed map for downstream compositing and inspection.
    links.new(color.outputs["Color"], shader.inputs["Base Color"])
    links.new(metal.outputs["Color"], shader.inputs["Metallic"])
    links.new(rough.outputs["Color"], shader.inputs["Roughness"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 1.0
    links.new(normal_image.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    for obj in parts:
        obj.data.materials.clear()
        obj.data.materials.append(material)

    # Render in the same neutral setup as the clay and UV checks.
    scene.render.filepath = str(BASE / "candidate_pbr.png")
    scene.cycles.samples = 64
    bpy.ops.render.render(write_still=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    report = {
        "blend": str(OUTPUT),
        "preview": str(BASE / "candidate_pbr.png"),
        "part_count": len(parts),
        "texture_resolution": "2048x2048",
        "packed_images": [node.image.name for node in (color, metal, rough, normal_image, ao, height)],
        "normal_convention": "OpenGL",
        "height_displacement_enabled": False,
        "ao_multiplied_into_base_color": False,
    }
    (BASE / "pbr_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("PBR_AUDIT=" + json.dumps(report))


main()
