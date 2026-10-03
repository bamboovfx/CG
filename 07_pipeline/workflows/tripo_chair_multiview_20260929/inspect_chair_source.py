"""Read-only audit of chair candidates in a Blender source file.

Input: opened .blend. Output: JSON summary printed to stdout.
"""

import bpy
import json


def summarize_object(obj):
    """Return name, type and collections for one scene object."""
    return {
        "name": obj.name,
        "type": obj.type,
        "collections": [collection.name for collection in obj.users_collection],
        "dimensions": [round(value, 4) for value in obj.dimensions],
    }


def main():
    """Print chair-related objects and collections from the opened file."""
    chair_objects = [
        summarize_object(obj)
        for obj in bpy.data.objects
        if any(token in obj.name.lower() for token in ("chair", "seat", "stool", "backrest"))
    ]
    chair_collections = [
        {"name": col.name, "objects": len(col.all_objects)}
        for col in bpy.data.collections
        if any(token in col.name.lower() for token in ("chair", "seat", "stool"))
    ]
    print("CHAIR_AUDIT_JSON=" + json.dumps({"objects": chair_objects, "collections": chair_collections}))


main()
