"""Convert a Tripo GLB to an FBX mesh for Substance Painter validation."""

import sys

import bpy


def main() -> None:
    """Import the input GLB and export selected meshes with UVs to FBX."""
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    source_path, output_path = arguments

    # Keep the conversion isolated from startup scene objects.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=source_path)

    # Painter needs the imported mesh and UVs; other scene objects are excluded.
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode="AUTO",
    )
    print(f"Exported {len(mesh_objects)} mesh object(s) to {output_path}")


if __name__ == "__main__":
    main()
