"""Inspect GLB geometry and texture metadata for the Tripo chair pilot."""

import argparse
import io
import json
import struct
from pathlib import Path

from PIL import Image


def read_glb(path):
    """Read GLB JSON and binary chunks from path; return both chunks."""
    with path.open("rb") as stream:
        header = stream.read(12)
        magic, version, length = struct.unpack("<4sII", header)
        if magic != b"glTF" or version != 2 or length != path.stat().st_size:
            raise ValueError("Invalid GLB v2 header")
        chunks = {}
        while stream.tell() < length:
            chunk_length, chunk_type = struct.unpack("<I4s", stream.read(8))
            chunks[chunk_type] = stream.read(chunk_length)
    return json.loads(chunks[b"JSON"]), chunks.get(b"BIN\x00", b"")


def image_report(document, binary):
    """Describe embedded images from GLB JSON and binary; return image records."""
    records = []
    for index, image in enumerate(document.get("images", [])):
        record = {"index": index, "name": image.get("name"), "mime_type": image.get("mimeType")}
        if "bufferView" in image:
            view = document["bufferViews"][image["bufferView"]]
            start = view.get("byteOffset", 0)
            payload = binary[start : start + view["byteLength"]]
            record["bytes"] = len(payload)
            try:
                with Image.open(io.BytesIO(payload)) as source:
                    record["size"] = list(source.size)
                    record["format"] = source.format
            except Exception as error:
                record["read_error"] = str(error)
        else:
            record["uri"] = image.get("uri")
        records.append(record)
    return records


def inspect(path):
    """Inspect GLB path; return counts, UV coverage, materials, and images."""
    document, binary = read_glb(path)
    accessors = document.get("accessors", [])
    primitives = [primitive for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])]
    materials = []
    for material in document.get("materials", []):
        pbr = material.get("pbrMetallicRoughness", {})
        materials.append(
            {
                "name": material.get("name"),
                "base_color_texture": pbr.get("baseColorTexture", {}).get("index"),
                "metallic_roughness_texture": pbr.get("metallicRoughnessTexture", {}).get("index"),
                "normal_texture": material.get("normalTexture", {}).get("index"),
                "occlusion_texture": material.get("occlusionTexture", {}).get("index"),
                "metallic_factor": pbr.get("metallicFactor"),
                "roughness_factor": pbr.get("roughnessFactor"),
            }
        )
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "scene_count": len(document.get("scenes", [])),
        "node_count": len(document.get("nodes", [])),
        "mesh_count": len(document.get("meshes", [])),
        "primitive_count": len(primitives),
        "index_count": sum(accessors[p["indices"]]["count"] for p in primitives if "indices" in p),
        "vertex_count": sum(accessors[p["attributes"]["POSITION"]]["count"] for p in primitives),
        "primitives_with_uv": sum("TEXCOORD_0" in p["attributes"] for p in primitives),
        "material_count": len(materials),
        "materials": materials,
        "images": image_report(document, binary),
        "extensions_used": document.get("extensionsUsed", []),
    }


def main():
    """Parse command-line paths and write the GLB metadata report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = inspect(args.input)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("mesh_count", "primitive_count", "index_count", "vertex_count", "material_count", "primitives_with_uv")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
