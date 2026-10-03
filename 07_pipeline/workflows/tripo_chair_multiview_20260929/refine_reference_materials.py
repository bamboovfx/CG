"""Refine the Tripo chair pilot materials against the photographed classroom chair.

Inputs: the earlier Painter/Blender candidate and the established Designer wood set.
Outputs: a separate reference-matched Blender candidate, preview, and audit.
"""

import bpy
import json
from pathlib import Path
from mathutils import Vector


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_multiview_20260929")
WOOD = Path("D:/00_projects/10_CG/Shot_Test/02_assets/textures/generated/wood_groups/school_board")
SOURCE = BASE / "tripo_chair_pbr_candidate.blend"
OUTPUT = BASE / "tripo_chair_reference_mat_candidate.blend"
PREVIEW = BASE / "candidate_reference_mat.png"
DETAIL = BASE / "candidate_reference_mat_detail.png"


def linear(value):
    """Convert one sRGB channel to Blender's linear shader value."""
    value = value / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def rgb(hex_color):
    """Convert a reference sRGB hex color to a linear RGBA socket value."""
    return tuple(linear(int(hex_color[index:index + 2], 16)) for index in (1, 3, 5)) + (1.0,)


def image_node(nodes, path, color_space, role):
    """Load one texture into a default-named node and pack it into the candidate."""
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = color_space
    image.pack()
    node = nodes.new("ShaderNodeTexImage")
    node.image = image
    node.extension = "REPEAT"
    node["role"] = role
    return node


def wood_material(name, across_axis):
    """Build directional school wood in object coordinates; X follows the grain."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    # Map in metres so the grain has the Designer material's documented 0.6 m period.
    position = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(position.outputs["Object"], separate.inputs["Vector"])
    across = nodes.new("ShaderNodeMath")
    across.operation = "MULTIPLY"
    across.inputs[1].default_value = 1.0 / 0.6
    links.new(separate.outputs[across_axis], across.inputs[0])
    along = nodes.new("ShaderNodeMath")
    along.operation = "MULTIPLY"
    along.inputs[1].default_value = 1.0 / 0.6
    links.new(separate.outputs["X"], along.inputs[0])
    coords = nodes.new("ShaderNodeCombineXYZ")
    links.new(across.outputs[0], coords.inputs["X"])
    links.new(along.outputs[0], coords.inputs["Y"])

    color = image_node(nodes, WOOD / "BaseColor.png", "sRGB", "Designer school board base color")
    rough = image_node(nodes, WOOD / "Roughness.png", "Non-Color", "Designer school board roughness")
    height = image_node(nodes, WOOD / "Height.png", "Non-Color", "Designer school board microheight")
    scratches = image_node(nodes, WOOD / "ScratchMask.png", "Non-Color", "Designer school board fine scratches")
    for node in (color, rough, height, scratches):
        links.new(coords.outputs["Vector"], node.inputs["Vector"])

    # The reference shows honey varnish with visible fine grain and a modest sheen.
    tone = nodes.new("ShaderNodeHueSaturation")
    tone.inputs["Saturation"].default_value = 1.20
    tone.inputs["Value"].default_value = 1.12
    links.new(color.outputs["Color"], tone.inputs["Color"])
    links.new(tone.outputs["Color"], shader.inputs["Base Color"])
    remap = nodes.new("ShaderNodeMapRange")
    remap.inputs["To Min"].default_value = 0.29
    remap.inputs["To Max"].default_value = 0.43
    links.new(rough.outputs["Color"], remap.inputs["Value"])
    scratch_rough = nodes.new("ShaderNodeMath")
    scratch_rough.operation = "MULTIPLY"
    scratch_rough.inputs[1].default_value = 0.12
    links.new(scratches.outputs["Color"], scratch_rough.inputs[0])
    combined_rough = nodes.new("ShaderNodeMath")
    combined_rough.operation = "ADD"
    combined_rough.use_clamp = True
    links.new(remap.outputs["Result"], combined_rough.inputs[0])
    links.new(scratch_rough.outputs[0], combined_rough.inputs[1])
    links.new(combined_rough.outputs[0], shader.inputs["Roughness"])
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Coat Weight"].default_value = 0.22
    shader.inputs["Coat Roughness"].default_value = 0.24
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.20
    bump.inputs["Distance"].default_value = 0.00015
    links.new(height.outputs["Color"], bump.inputs["Height"])
    scratch_bump = nodes.new("ShaderNodeBump")
    scratch_bump.inputs["Strength"].default_value = 0.10
    scratch_bump.inputs["Distance"].default_value = 0.000025
    links.new(scratches.outputs["Color"], scratch_bump.inputs["Height"])
    links.new(bump.outputs["Normal"], scratch_bump.inputs["Normal"])
    links.new(scratch_bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def painted_steel_material(pilot, name, wear_strength):
    """Keep Painter detail and add sparse, region-scaled paint chips."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    # Reuse the Painter atlas; only the darkest chips expose the metal substrate.
    source = next(node.image for node in pilot.node_tree.nodes if node.get("role") == "Base Color / sRGB")
    source_normal = next(node.image for node in pilot.node_tree.nodes if node.get("role") == "Normal OpenGL / linear")
    color = nodes.new("ShaderNodeTexImage")
    color.image = source
    color["role"] = "Painter color as sparse damage source"
    luminance = nodes.new("ShaderNodeRGBToBW")
    links.new(color.outputs["Color"], luminance.inputs["Color"])
    select = nodes.new("ShaderNodeValToRGB")
    select.color_ramp.elements[0].position = 0.33
    select.color_ramp.elements[0].color = (1, 1, 1, 1)
    select.color_ramp.elements[1].position = 0.60
    select.color_ramp.elements[1].color = (0, 0, 0, 1)
    links.new(luminance.outputs["Val"], select.inputs["Fac"])
    subdued = nodes.new("ShaderNodeMath")
    subdued.operation = "MULTIPLY"
    subdued.inputs[1].default_value = 0.70
    links.new(select.outputs["Color"], subdued.inputs[0])
    blend = nodes.new("ShaderNodeMixRGB")
    blend.blend_type = "MIX"
    blend.inputs[1].default_value = rgb("#D1CEBC")
    links.new(subdued.outputs[0], blend.inputs[0])
    links.new(color.outputs["Color"], blend.inputs[2])
    # Fine chips are clustered rather than evenly scattered on every tube.
    position = nodes.new("ShaderNodeTexCoord")
    fine_noise = nodes.new("ShaderNodeTexNoise")
    fine_noise.inputs["Scale"].default_value = 125.0
    fine_noise.inputs["Detail"].default_value = 2.0
    links.new(position.outputs["Object"], fine_noise.inputs["Vector"])
    fine_select = nodes.new("ShaderNodeValToRGB")
    fine_select.color_ramp.elements[0].position = 0.66
    fine_select.color_ramp.elements[0].color = (0, 0, 0, 1)
    fine_select.color_ramp.elements[1].position = 0.74
    fine_select.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(fine_noise.outputs["Fac"], fine_select.inputs["Fac"])
    cluster_noise = nodes.new("ShaderNodeTexNoise")
    cluster_noise.inputs["Scale"].default_value = 7.0
    links.new(position.outputs["Object"], cluster_noise.inputs["Vector"])
    cluster_select = nodes.new("ShaderNodeValToRGB")
    cluster_select.color_ramp.elements[0].position = 0.42
    cluster_select.color_ramp.elements[0].color = (0, 0, 0, 1)
    cluster_select.color_ramp.elements[1].position = 0.60
    cluster_select.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(cluster_noise.outputs["Fac"], cluster_select.inputs["Fac"])
    cluster_mask = nodes.new("ShaderNodeMath")
    cluster_mask.operation = "MULTIPLY"
    links.new(fine_select.outputs["Color"], cluster_mask.inputs[0])
    links.new(cluster_select.outputs["Color"], cluster_mask.inputs[1])
    wear = nodes.new("ShaderNodeMath")
    wear.operation = "MULTIPLY"
    wear.inputs[1].default_value = wear_strength
    links.new(cluster_mask.outputs[0], wear.inputs[0])
    chip_color = nodes.new("ShaderNodeMixRGB")
    chip_color.blend_type = "MIX"
    chip_color.inputs[2].default_value = rgb("#5C5851")
    links.new(wear.outputs[0], chip_color.inputs[0])
    links.new(blend.outputs["Color"], chip_color.inputs[1])
    links.new(chip_color.outputs["Color"], shader.inputs["Base Color"])

    # The intact ivory enamel is nonmetallic; exposed substrate is dark steel.
    metal = nodes.new("ShaderNodeMath")
    metal.operation = "MULTIPLY"
    metal.inputs[1].default_value = 0.84
    links.new(wear.outputs[0], metal.inputs[0])
    links.new(metal.outputs[0], shader.inputs["Metallic"])
    shader.inputs["Roughness"].default_value = 0.38
    normal_image = nodes.new("ShaderNodeTexImage")
    normal_image.image = source_normal
    normal_image["role"] = "Painter OpenGL normal, reduced wear strength"
    normal = nodes.new("ShaderNodeNormalMap")
    normal.space = "TANGENT"
    normal.inputs["Strength"].default_value = 0.35
    links.new(normal_image.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    return material


def plain_material(name, color, metallic, roughness):
    """Create a small-part finish where the atlas would blur or merge the part."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = rgb(color)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def main():
    """Assign reference-based finishes to Tripo parts and save a distinct pilot."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    parts = [obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")]
    assert len(parts) == 26, f"Expected 26 chair parts, found {len(parts)}"
    # Use transformed world bounds: part-local dimensions are rotated by FBX import.
    min_z = min((obj.matrix_world @ Vector(corner)).z for obj in parts for corner in obj.bound_box)
    max_z = max((obj.matrix_world @ Vector(corner)).z for obj in parts for corner in obj.bound_box)
    assert abs(min_z) < 0.001 and abs(max_z - 0.8045) < 0.001, (min_z, max_z)
    pilot = bpy.data.materials["SP classroom chair PBR pilot"]
    seat = wood_material("Reference school wood seat", "Z")
    back = wood_material("Reference school wood back", "Y")
    steel = painted_steel_material(pilot, "Reference aged ivory painted steel", 0.52)
    exposed_steel = painted_steel_material(pilot, "Reference aged ivory painted steel / contact areas", 0.82)
    fastener = plain_material("Reference zinc fasteners", "#A9ABA8", 0.82, 0.31)
    foot = plain_material("Reference aged ivory foot cap", "#C6BE9C", 0.0, 0.56)
    assignments = {}
    for obj in parts:
        # Material-ID render confirms part 02 is the seat and part 04 the bent back tube.
        if obj.name == "LP_part_02":
            material = seat
        elif obj.name == "LP_part_09":
            material = back
        elif obj.name == "LP_part_00":
            material = foot
        elif obj.name in {"LP_part_03", "LP_part_06", "LP_part_07", "LP_part_10", "LP_part_11", "LP_part_12", "LP_part_14", "LP_part_15", "LP_part_17", "LP_part_18", "LP_part_19", "LP_part_20"}:
            material = fastener
        elif obj.name in {"LP_part_04", "LP_part_22", "LP_part_23", "LP_part_24"}:
            material = exposed_steel
        else:
            material = steel
        obj.data.materials.clear()
        obj.data.materials.append(material)
        assignments[obj.name] = material.name

    # Match the previous neutral candidate camera for an honest before/after check.
    scene.render.filepath = str(PREVIEW)
    scene.cycles.samples = 96
    bpy.ops.render.render(write_still=True)
    # Inspect board grain, fasteners and paint chips at a larger screen scale.
    camera = scene.camera
    full_location = camera.location.copy()
    full_scale = camera.data.ortho_scale
    full_width = scene.render.resolution_x
    full_height = scene.render.resolution_y
    camera.location.z += 0.18
    camera.data.ortho_scale = 0.72
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.filepath = str(DETAIL)
    bpy.ops.render.render(write_still=True)
    camera.location = full_location
    camera.data.ortho_scale = full_scale
    scene.render.resolution_x = full_width
    scene.render.resolution_y = full_height
    scene.render.filepath = str(PREVIEW)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    audit = {
        "source": str(SOURCE),
        "output": str(OUTPUT),
        "preview": str(PREVIEW),
        "detail_preview": str(DETAIL),
        "reference": "01_preproduction/references/props/20160220_201e63.JPG",
        "designer_wood": str(WOOD),
        "wood_period_m": 0.6,
        "painted_coating_metallic": 0,
        "up_axis": "Z",
        "world_height_m": max_z - min_z,
        "lowest_vertex_z_m": min((obj.matrix_world @ Vector(corner)).z for obj in parts for corner in obj.bound_box),
        "object_space_texture_mapping": True,
        "painter_damage_reduced": True,
        "part_materials": assignments,
    }
    (BASE / "reference_mat_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REFERENCE_MAT_AUDIT=" + json.dumps(audit, ensure_ascii=False))


main()
