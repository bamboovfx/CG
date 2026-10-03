"""Bake the authored Tripo chair materials into two UV texture sets.

Run with ``-- 512`` for a pipeline test, ``-- 4096`` for a full bake, or
``-- repair`` to rebuild the final mesh while rebaking Normal/AO only, or
``-- color`` to update the wood BaseColor after a seat-figure revision.
The plain fastener and detached foot-cap materials remain parameter based.
"""

import bpy
import hashlib
import json
import sys
from pathlib import Path


BASE = Path("D:/00_projects/10_CG/Shot_Test/07_pipeline/cache/tripo_chair_material_v2_20260930")
SOURCE = BASE / "chair_material_v2_uv.blend"
WOOD_PARTS = {"LP_part_02", "LP_part_09"}
PLAIN_PARTS = {"LP_part_00", "LP_part_03", "LP_part_06", "LP_part_07", "LP_part_10", "LP_part_11", "LP_part_12", "LP_part_14", "LP_part_15", "LP_part_17", "LP_part_18", "LP_part_19", "LP_part_20"}
CHANNELS = ("BaseColor", "Roughness", "Metallic", "Normal_OpenGL", "AO")


def sha256(path):
    """Return the SHA256 of one saved file without loading it all at once."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def triangulate(objects):
    """Freeze triangle direction while retaining the Tripo mesh split normals."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new("Triangulate", "TRIANGULATE")
        modifier.quad_method = "BEAUTY"
        # Tripo seat shading changes visibly if its imported custom normals are lost.
        modifier.keep_custom_normals = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.select_all(action="DESELECT")


def group_materials(objects):
    """Return each material slot used by one texture set, without duplicates."""
    return list({material.name: material for obj in objects for material in obj.data.materials if material}.values())


def target_node(material, target_image):
    """Make one default-named image node the active bake target."""
    nodes = material.node_tree.nodes
    for node in nodes:
        node.select = False
    target = next((node for node in nodes if node.get("role") == "UV bake target"), None)
    if target is None:
        target = nodes.new("ShaderNodeTexImage")
        target["role"] = "UV bake target"
    target.image = target_image
    target.select = True
    nodes.active = target


def emit_channel(material, channel):
    """Temporarily route a Principled input into emission for an exact data bake."""
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL" and node.is_active_output)
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    previous = output.inputs["Surface"].links[0].from_socket
    source = shader.inputs[channel]
    emission = nodes.new("ShaderNodeEmission")
    if source.is_linked:
        links.new(source.links[0].from_socket, emission.inputs["Color"])
    else:
        value = source.default_value
        emission.inputs["Color"].default_value = (value, value, value, 1) if isinstance(value, float) else value
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs[0], output.inputs["Surface"])
    return output, previous, emission


def restore_channel(material, temporary):
    """Restore the authored material output after one emission bake."""
    output, previous, emission = temporary
    material.node_tree.links.new(previous, output.inputs["Surface"])
    material.node_tree.nodes.remove(emission)


def bake_group(name, objects, resolution, texture_dir, channels=CHANNELS):
    """Bake the requested maps for one UV texture set."""
    scene = bpy.context.scene
    materials = group_materials(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    output = {}
    for channel in channels:
        filename = texture_dir / f"Chair_{name}_{channel}.png"
        target_image = bpy.data.images.new(f"Bake {name} {channel}", width=resolution, height=resolution, alpha=False)
        target_image.colorspace_settings.name = "sRGB" if channel == "BaseColor" else "Non-Color"
        for material in materials:
            target_node(material, target_image)
        temporaries = {}
        if channel in {"BaseColor", "Roughness", "Metallic"}:
            socket = {"BaseColor": "Base Color", "Roughness": "Roughness", "Metallic": "Metallic"}[channel]
            temporaries = {material.name: emit_channel(material, socket) for material in materials}
            bake_type = "EMIT"
        elif channel == "Normal_OpenGL":
            bake_type = "NORMAL"
        else:
            bake_type = "AO"
        for material in materials:
            target_node(material, target_image)
        scene.render.bake.margin = max(2, resolution // 256)
        scene.render.bake.use_clear = True
        bpy.ops.object.bake(type=bake_type)
        for material in materials:
            if material.name in temporaries:
                restore_channel(material, temporaries[material.name])
        target_image.filepath_raw = str(filename)
        target_image.file_format = "PNG"
        target_image.save()
        output[channel] = {"path": str(filename), "sha256": sha256(filename)}
        print(f"BAKED={name}/{channel}/{resolution}", flush=True)
        for material in materials:
            target = next(node for node in material.node_tree.nodes if node.get("role") == "UV bake target")
            target.image = None
        bpy.data.images.remove(target_image)
    bpy.ops.object.select_all(action="DESELECT")
    return output


def baked_material(name, paths, coat):
    """Build a portable Principled material from one baked PBR texture set."""
    material = bpy.data.materials.new(f"Baked {name} PBR")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UV_Material"
    images = {}
    for channel in CHANNELS:
        data = bpy.data.images.load(paths[channel]["path"], check_existing=False)
        data.colorspace_settings.name = "sRGB" if channel == "BaseColor" else "Non-Color"
        data.pack()
        node = nodes.new("ShaderNodeTexImage")
        node.image = data
        node["role"] = channel
        links.new(uv.outputs["UV"], node.inputs["Vector"])
        images[channel] = node
    links.new(images["BaseColor"].outputs["Color"], shader.inputs["Base Color"])
    links.new(images["Roughness"].outputs["Color"], shader.inputs["Roughness"])
    links.new(images["Metallic"].outputs["Color"], shader.inputs["Metallic"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.space = "TANGENT"
    links.new(images["Normal_OpenGL"].outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    # AO remains separate data; it is not baked into the diffuse albedo.
    if coat:
        shader.inputs["Coat Weight"].default_value = 0.26
        shader.inputs["Coat Roughness"].default_value = 0.24
    return material


def main():
    """Bake, reopen as UV PBR, render, export, and record the final candidate."""
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    repair = bool(arguments and arguments[0] == "repair")
    color_update = bool(arguments and arguments[0] == "color")
    resolution = 4096 if repair or color_update else (int(arguments[0]) if arguments else 4096)
    assert resolution in {512, 4096}
    testing = resolution != 4096
    texture_dir = BASE / ("textures_test" if testing else "textures")
    texture_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    parts = sorted((obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith("LP_part_")), key=lambda obj: obj.name)
    assert len(parts) == 26
    wood = [obj for obj in parts if obj.name in WOOD_PARTS]
    paint = [obj for obj in parts if obj.name not in WOOD_PARTS | PLAIN_PARTS]
    triangulate(parts)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24 if testing else 48
    scene.render.bake.target = "IMAGE_TEXTURES"
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.normal_space = "TANGENT"
    if repair or color_update:
        # Reuse checked channels and bake only maps affected by the revision.
        maps = json.loads((BASE / "bake_audit.json").read_text(encoding="utf-8"))["texture_sets"]
        if repair:
            for name, objects in (("Wood", wood), ("Paint", paint)):
                maps[name].update(bake_group(name, objects, resolution, texture_dir, ("Normal_OpenGL", "AO")))
        else:
            maps["Wood"].update(bake_group("Wood", wood, resolution, texture_dir, ("BaseColor",)))
    else:
        maps = {"Wood": bake_group("Wood", wood, resolution, texture_dir), "Paint": bake_group("Paint", paint, resolution, texture_dir)}
    wood_baked = baked_material("Wood", maps["Wood"], True)
    paint_baked = baked_material("Paint", maps["Paint"], False)
    for obj in wood:
        obj.data.materials.clear()
        obj.data.materials.append(wood_baked)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
    for obj in paint:
        obj.data.materials.clear()
        obj.data.materials.append(paint_baked)
        for polygon in obj.data.polygons:
            polygon.material_index = 0

    # The same neutral setup exposes texture-bake color or normal mismatches.
    scene.cycles.samples = 96
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.filepath = str(BASE / ("baked_test_overview.png" if testing else "baked_overview.png"))
    bpy.ops.render.render(write_still=True)
    camera = scene.camera
    original_location = camera.location.copy()
    original_scale = camera.data.ortho_scale
    camera.location.z += 0.18
    camera.data.ortho_scale = 0.72
    scene.render.filepath = str(BASE / ("baked_test_detail.png" if testing else "baked_detail.png"))
    bpy.ops.render.render(write_still=True)
    camera.location = original_location
    camera.data.ortho_scale = original_scale
    scene.render.filepath = str(BASE / ("baked_test_overview.png" if testing else "baked_overview.png"))
    blend = BASE / ("chair_material_v2_baked_test.blend" if testing else "chair_material_v2_baked.blend")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if not testing:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in parts:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.export_scene.fbx(filepath=str(BASE / "chair_material_v2_low.fbx"), use_selection=True, object_types={"MESH"}, apply_unit_scale=True, bake_space_transform=False, path_mode="AUTO")
    audit = {"source": str(SOURCE), "blend": str(blend), "resolution": resolution, "normal_convention": "OpenGL tangent", "ao_separate": True, "triangulated_final_mesh": True, "texture_sets": maps}
    (BASE / ("bake_test_audit.json" if testing else "bake_audit.json")).write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print("BAKE_AUDIT=" + json.dumps(audit), flush=True)


main()
