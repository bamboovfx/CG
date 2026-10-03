"""Summarize the Painter-exported glTF PBR maps without changing their pixels."""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def image_summary(path):
    """Read one image path and return dimensions plus channel distribution statistics."""
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB"), dtype=np.uint8)
        return {
            "file": path.name,
            "size": list(image.size),
            "mode": image.mode,
            "channels": [
                {
                    "mean": round(float(pixels[:, :, channel].mean()), 2),
                    "min": int(pixels[:, :, channel].min()),
                    "max": int(pixels[:, :, channel].max()),
                    "near_zero_fraction": round(float(np.mean(pixels[:, :, channel] <= 10)), 4),
                    "near_one_fraction": round(float(np.mean(pixels[:, :, channel] >= 245)), 4),
                }
                for channel in range(3)
            ],
        }


def main(folder, output_path):
    """Summarize all exported PNGs in folder and write output_path as JSON."""
    summaries = [image_summary(path) for path in sorted(folder.glob("*.png"))]
    output_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"Audited {len(summaries)} PBR maps")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
