"""Unpack glTF metallic-roughness channels for Painter resource inputs."""

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    """Write byte-preserving green roughness and blue metallic channels as PNGs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # glTF stores perceptual roughness in G and metallic weight in B.
    with Image.open(args.input) as packed:
        red, roughness, metallic = packed.convert("RGB").split()
        roughness.save(args.output_dir / "tripo_chair_roughness_source.png")
        metallic.save(args.output_dir / "tripo_chair_metallic_source.png")
        print(f"Input size: {packed.size}; red channel intentionally unused")
        print(f"Roughness range: {roughness.getextrema()}")
        print(f"Metallic range: {metallic.getextrema()}")


if __name__ == "__main__":
    main()
