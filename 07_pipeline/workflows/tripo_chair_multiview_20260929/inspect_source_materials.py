"""List existing classroom chair materials without editing its source blend."""

import bpy
import json
from pathlib import Path


SOURCE = Path("D:/00_projects/10_CG/Shot_Test/02_assets/work/classroom_props.blend")


def main():
    """Report material names and chair object assignments from the source asset."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    report = []
    for material in bpy.data.materials:
        if material.name.startswith("chair_") or material.name.startswith("Wood / 01"):
            report.append({"name": material.name, "node_count": len(material.node_tree.nodes) if material.use_nodes else 0})
    print("MATERIALS=" + json.dumps(report))


main()
