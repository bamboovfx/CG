"""Extract embedded Tripo GLB textures without changing their bytes."""

import argparse
from pathlib import Path

from inspect_glb import read_glb


def main() -> None:
    """Write each embedded image next to the GLB for inspection and Painter import."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    document, binary = read_glb(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # The GLB buffer views hold the original encoded JPEG or PNG data.
    for index, image in enumerate(document.get("images", [])):
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start : start + view["byteLength"]]
        extension = ".png" if image.get("mimeType") == "image/png" else ".jpg"
        target = args.output_dir / f"{args.input.stem}_image_{index}{extension}"
        target.write_bytes(payload)
        print(f"{index}: {target} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
