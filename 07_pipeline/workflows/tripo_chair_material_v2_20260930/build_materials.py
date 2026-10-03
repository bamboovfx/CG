"""Build new chair materials from real-chair evidence on the Tripo mesh.

The input is the unpainted Tripo UV candidate. The old Blender chair materials,
old Painter exports and previous lookdev candidate are intentionally not read.
"""

import bpy
import json
from pathlib import Path


ROOT = Path("D:/00_projects/10_CG/Shot_Test")
BASE = ROOT / "07_pipeline/cache/tripo_chair_material_v2_20260930"
INPUT = ROOT / "07_pipeline/cache/tripo_chair_multiview_20260929/tripo_chair_blender_candidate.blend"
WOOD = ROOT / "02_assets/textures/generated/wood_groups/school_board"
OUTPUT = BASE / "chair_material_v2_working.blend"
OVERVIEW = BASE / "material_v2_overview.png"
DETAIL = BASE / "material_v2_detail.png"


def linear(value):
    """Return a Blender linear channel from an 8-bit sRGB channel."""
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def color(hex_value):
    """Return one linear RGBA value from a reference palette hex string."""
    return tuple(linear(int(hex_value[index:index + 2], 16)) for index in (1, 3, 5)) + (1.0,)


def image(nodes, filename, color_space, role):
    """Load a licensed project texture, pack it, and return its image node."""
    data = bpy.data.images.load(str(WOOD / filename), check_existing=True)
    data.colorspace_settings.name = color_space
    data.pack()
    node = nodes.new("ShaderNodeTexImage")
    node.image = data
    node.extension = "REPEAT"
    node["role"] = role
    return node


def multiply(nodes, links, source, factor):
    """Create a default-named math multiplier for a shader scalar."""
    node = nodes.new("ShaderNodeMath")
    node.operation = "MULTIPLY"
    node.inputs[1].default_value = factor
    links.new(source, node.inputs[0])
    return node.outputs[0]


def make_wood(name, across_axis, thickness_axis, figure_scale, distortion, figure_mix, figure_dark="#B97530", figure_light="#D79543"):
    """Create a board-face, varnish and plywood-edge shader for one board."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    # Local coordinates lock the grain to the chair when it moves into a shot.
    coordinates = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coordinates.outputs["Object"], separate.inputs["Vector"])
    mapped = nodes.new("ShaderNodeCombineXYZ")
    links.new(multiply(nodes, links, separate.outputs[across_axis], 1.0 / 0.6), mapped.inputs["X"])
    links.new(multiply(nodes, links, separate.outputs["X"], 1.0 / 0.6), mapped.inputs["Y"])
    wood_color = image(nodes, "BaseColor.png", "sRGB", "CC0 plywood / Designer fine grain")
    wood_rough = image(nodes, "Roughness.png", "Non-Color", "Designer wood roughness")
    wood_height = image(nodes, "Height.png", "Non-Color", "Designer wood microheight")
    scratches = image(nodes, "ScratchMask.png", "Non-Color", "Designer thin varnish scratches")
    for node in (wood_color, wood_rough, wood_height, scratches):
        links.new(mapped.outputs["Vector"], node.inputs["Vector"])

    # A broad, curved figure is present on the photographed seat, unlike generic fine grain.
    figure = nodes.new("ShaderNodeTexWave")
    figure.wave_type = "BANDS"
    figure.bands_direction = "X"
    figure.inputs["Scale"].default_value = figure_scale
    figure.inputs["Distortion"].default_value = distortion
    figure.inputs["Detail"].default_value = 2.0
    figure.inputs["Detail Scale"].default_value = 1.2
    links.new(mapped.outputs["Vector"], figure.inputs["Vector"])
    figure_tone = nodes.new("ShaderNodeValToRGB")
    figure_tone.color_ramp.elements[0].position = 0.22
    figure_tone.color_ramp.elements[0].color = color(figure_dark)
    figure_tone.color_ramp.elements[1].position = 0.76
    figure_tone.color_ramp.elements[1].color = color(figure_light)
    links.new(figure.outputs["Fac"], figure_tone.inputs["Fac"])
    face_mix = nodes.new("ShaderNodeMixRGB")
    face_mix.blend_type = "MIX"
    face_mix.inputs[0].default_value = figure_mix
    links.new(wood_color.outputs["Color"], face_mix.inputs[1])
    links.new(figure_tone.outputs["Color"], face_mix.inputs[2])
    warm = nodes.new("ShaderNodeHueSaturation")
    warm.inputs["Saturation"].default_value = 1.35
    warm.inputs["Value"].default_value = 1.04
    links.new(face_mix.outputs["Color"], warm.inputs["Color"])

    # Board edges expose warm, fine plywood laminations instead of a wrapped face image.
    layer_phase = multiply(nodes, links, separate.outputs[thickness_axis], 2.0 * 3.14159265 / 0.0068)
    layer_sine = nodes.new("ShaderNodeMath")
    layer_sine.operation = "SINE"
    links.new(layer_phase, layer_sine.inputs[0])
    edge_lines = nodes.new("ShaderNodeValToRGB")
    edge_lines.color_ramp.elements[0].position = 0.44
    edge_lines.color_ramp.elements[0].color = color("#A77137")
    edge_lines.color_ramp.elements[1].position = 0.56
    edge_lines.color_ramp.elements[1].color = color("#BD894A")
    normalized_sine = nodes.new("ShaderNodeMapRange")
    normalized_sine.inputs["From Min"].default_value = -1.0
    normalized_sine.inputs["From Max"].default_value = 1.0
    links.new(layer_sine.outputs[0], normalized_sine.inputs["Value"])
    links.new(normalized_sine.outputs["Result"], edge_lines.inputs["Fac"])

    normal = nodes.new("ShaderNodeNewGeometry")
    local_normal = nodes.new("ShaderNodeVectorTransform")
    local_normal.vector_type = "NORMAL"
    local_normal.convert_from = "WORLD"
    local_normal.convert_to = "OBJECT"
    links.new(normal.outputs["Normal"], local_normal.inputs["Vector"])
    normal_axis = nodes.new("ShaderNodeSeparateXYZ")
    links.new(local_normal.outputs["Vector"], normal_axis.inputs["Vector"])
    facing = nodes.new("ShaderNodeMath")
    facing.operation = "ABSOLUTE"
    links.new(normal_axis.outputs[thickness_axis], facing.inputs[0])
    face_weight = nodes.new("ShaderNodeMapRange")
    face_weight.inputs["From Min"].default_value = 0.30
    face_weight.inputs["From Max"].default_value = 0.82
    links.new(facing.outputs[0], face_weight.inputs["Value"])
    final_color = nodes.new("ShaderNodeMixRGB")
    links.new(face_weight.outputs["Result"], final_color.inputs[0])
    links.new(edge_lines.outputs["Color"], final_color.inputs[1])
    links.new(warm.outputs["Color"], final_color.inputs[2])
    links.new(final_color.outputs["Color"], shader.inputs["Base Color"])

    # Clear varnish changes reflection more than it changes the painted wood color.
    rough_range = nodes.new("ShaderNodeMapRange")
    rough_range.inputs["To Min"].default_value = 0.27
    rough_range.inputs["To Max"].default_value = 0.41
    links.new(wood_rough.outputs["Color"], rough_range.inputs["Value"])
    scratch_rough = multiply(nodes, links, scratches.outputs["Color"], 0.09)
    rough_sum = nodes.new("ShaderNodeMath")
    rough_sum.operation = "ADD"
    links.new(rough_range.outputs["Result"], rough_sum.inputs[0])
    links.new(scratch_rough, rough_sum.inputs[1])
    links.new(rough_sum.outputs[0], shader.inputs["Roughness"])
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Coat Weight"].default_value = 0.26
    shader.inputs["Coat Roughness"].default_value = 0.24
    grain_bump = nodes.new("ShaderNodeBump")
    grain_bump.inputs["Strength"].default_value = 0.18
    grain_bump.inputs["Distance"].default_value = 0.00011
    links.new(wood_height.outputs["Color"], grain_bump.inputs["Height"])
    scratch_bump = nodes.new("ShaderNodeBump")
    scratch_bump.inputs["Strength"].default_value = 0.10
    scratch_bump.inputs["Distance"].default_value = 0.000018
    links.new(scratches.outputs["Color"], scratch_bump.inputs["Height"])
    links.new(grain_bump.outputs["Normal"], scratch_bump.inputs["Normal"])
    links.new(scratch_bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_paint(name, wear_strength):
    """Build a dielectric ivory enamel with clustered steel and rust chips."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    coordinates = nodes.new("ShaderNodeTexCoord")
    fine = nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 115.0
    fine.inputs["Detail"].default_value = 2.0
    links.new(coordinates.outputs["Object"], fine.inputs["Vector"])
    fine_gate = nodes.new("ShaderNodeValToRGB")
    fine_gate.color_ramp.elements[0].position = 0.66
    fine_gate.color_ramp.elements[0].color = (0, 0, 0, 1)
    fine_gate.color_ramp.elements[1].position = 0.75
    fine_gate.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(fine.outputs["Fac"], fine_gate.inputs["Fac"])
    cluster = nodes.new("ShaderNodeTexNoise")
    cluster.inputs["Scale"].default_value = 8.0
    links.new(coordinates.outputs["Object"], cluster.inputs["Vector"])
    cluster_gate = nodes.new("ShaderNodeValToRGB")
    cluster_gate.color_ramp.elements[0].position = 0.43
    cluster_gate.color_ramp.elements[0].color = (0, 0, 0, 1)
    cluster_gate.color_ramp.elements[1].position = 0.59
    cluster_gate.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(cluster.outputs["Fac"], cluster_gate.inputs["Fac"])
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    links.new(fine_gate.outputs["Color"], both.inputs[0])
    links.new(cluster_gate.outputs["Color"], both.inputs[1])
    wear = multiply(nodes, links, both.outputs[0], wear_strength)

    # A second low-frequency mask makes only some exposed steel oxidized.
    rust_noise = nodes.new("ShaderNodeTexNoise")
    rust_noise.inputs["Scale"].default_value = 26.0
    links.new(coordinates.outputs["Object"], rust_noise.inputs["Vector"])
    rust_gate = nodes.new("ShaderNodeValToRGB")
    rust_gate.color_ramp.elements[0].position = 0.55
    rust_gate.color_ramp.elements[0].color = (0, 0, 0, 1)
    rust_gate.color_ramp.elements[1].position = 0.69
    rust_gate.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(rust_noise.outputs["Fac"], rust_gate.inputs["Fac"])
    rust = nodes.new("ShaderNodeMath")
    rust.operation = "MULTIPLY"
    links.new(wear, rust.inputs[0])
    links.new(rust_gate.outputs["Color"], rust.inputs[1])

    steel_mix = nodes.new("ShaderNodeMixRGB")
    steel_mix.inputs[1].default_value = color("#C9C6B8")
    steel_mix.inputs[2].default_value = color("#686B6B")
    links.new(wear, steel_mix.inputs[0])
    rust_mix = nodes.new("ShaderNodeMixRGB")
    rust_mix.inputs[2].default_value = color("#754C31")
    links.new(rust.outputs[0], rust_mix.inputs[0])
    links.new(steel_mix.outputs["Color"], rust_mix.inputs[1])
    links.new(rust_mix.outputs["Color"], shader.inputs["Base Color"])
    metal = nodes.new("ShaderNodeMath")
    metal.operation = "SUBTRACT"
    links.new(wear, metal.inputs[0])
    links.new(rust.outputs[0], metal.inputs[1])
    links.new(metal.outputs[0], shader.inputs["Metallic"])

    rough_steel = nodes.new("ShaderNodeMixRGB")
    rough_steel.inputs[1].default_value = (0.39, 0.39, 0.39, 1)
    rough_steel.inputs[2].default_value = (0.46, 0.46, 0.46, 1)
    links.new(wear, rough_steel.inputs[0])
    rough_rust = nodes.new("ShaderNodeMixRGB")
    rough_rust.inputs[2].default_value = (0.72, 0.72, 0.72, 1)
    links.new(rust.outputs[0], rough_rust.inputs[0])
    links.new(rough_steel.outputs["Color"], rough_rust.inputs[1])
    links.new(rough_rust.outputs["Color"], shader.inputs["Roughness"])
    peel = nodes.new("ShaderNodeTexNoise")
    peel.inputs["Scale"].default_value = 360.0
    links.new(coordinates.outputs["Object"], peel.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.000015
    links.new(peel.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_plain(name, hex_color, metallic, roughness):
    """Create a distinct fastener, plate or plastic foot-cap finish."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color(hex_color)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def main():
    """Assign the new reference-led materials and save neutral preview images."""
    BASE.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(INPUT))
    scene = bpy.context.scene
    parts = sorted((obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")), key=lambda obj: obj.name)
    assert len(parts) == 26, len(parts)
    seat = make_wood("AITA honey varnish / seat", "Z", "Y", 3.0, 6.0, 0.32, "#A56329", "#DEA04B")
    back = make_wood("AITA honey varnish / back", "Y", "Z", 5.0, 0.3, 0.10)
    paint = make_paint("AITA aged ivory enamel", 0.40)
    contact_paint = make_paint("AITA aged ivory enamel contact areas", 0.88)
    plate = make_plain("AITA cool grey back plates", "#9A9D98", 0.65, 0.44)
    screw = make_plain("AITA dark fastener heads", "#353535", 0.55, 0.43)
    foot = make_plain("AITA yellowed matte foot caps", "#C4BA91", 0.0, 0.64)
    assignments = {}
    for obj in parts:
        if obj.name == "LP_part_02":
            material = seat
        elif obj.name == "LP_part_09":
            material = back
        elif obj.name in {"LP_part_08", "LP_part_16"}:
            material = plate
        elif obj.name in {"LP_part_03", "LP_part_06", "LP_part_07", "LP_part_10", "LP_part_11", "LP_part_12", "LP_part_14", "LP_part_15", "LP_part_17", "LP_part_18", "LP_part_19", "LP_part_20"}:
            material = screw
        elif obj.name == "LP_part_00":
            material = foot
        elif obj.name in {"LP_part_04", "LP_part_22", "LP_part_23", "LP_part_24"}:
            material = contact_paint
        else:
            material = paint
        obj.data.materials.clear()
        obj.data.materials.append(material)
        assignments[obj.name] = material.name

    # The front-leg meshes include cap-like end faces; give only their low faces plastic.
    for name in ("LP_part_01", "LP_part_13", "LP_part_21", "LP_part_25"):
        obj = bpy.data.objects[name]
        obj.data.materials.append(foot)
        for polygon in obj.data.polygons:
            heights = [(obj.matrix_world @ obj.data.vertices[index].co).z for index in polygon.vertices]
            if max(heights) < 0.027:
                polygon.material_index = 1

    # A fixed neutral setup isolates material differences from shot lighting.
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OVERVIEW)
    bpy.ops.render.render(write_still=True)
    camera = scene.camera
    original_location = camera.location.copy()
    original_scale = camera.data.ortho_scale
    camera.location.z += 0.18
    camera.data.ortho_scale = 0.72
    scene.render.filepath = str(DETAIL)
    bpy.ops.render.render(write_still=True)
    camera.location = original_location
    camera.data.ortho_scale = original_scale
    scene.render.filepath = str(OVERVIEW)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    audit = {
        "input": str(INPUT),
        "output": str(OUTPUT),
        "reference_page": "https://aita.ocnk.net/product/3087",
        "reference_images_used_only_for_observation": True,
        "designer_wood_inputs": str(WOOD),
        "wood_period_m": 0.6,
        "parts": assignments,
        "maps_baked_to_uv": False,
    }
    (BASE / "material_v2_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MATERIAL_V2_AUDIT=" + json.dumps(audit, ensure_ascii=False))


main()
