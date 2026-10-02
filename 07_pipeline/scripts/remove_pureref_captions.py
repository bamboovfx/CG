"""Remove generated caption SVG items from a PureRef 2.1 scene copy.

PureRef stores its SQLite header page at the end of the scene. This script
temporarily restores the page order, edits only caption records, and writes a
candidate; the original scene is never changed here.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


PAGE_SIZE = 4096


def remove_captions(source: Path, candidate: Path, database_copy: Path) -> None:
    """Delete caption images and items while preserving all other scene rows."""
    raw = bytearray(source.read_bytes())
    expected = raw[40:104].decode("utf-16-be")
    assert expected == hashlib.md5(raw[104:]).hexdigest(), "Source checksum mismatch"

    # Reassemble the SQLite header and pointer-map pages from PureRef's trailer.
    header_offset = raw.find(b"SQLite format 3")
    assert header_offset > 2 * PAGE_SIZE and header_offset % PAGE_SIZE == 0
    pointer_map_bytes = len(raw) - header_offset - PAGE_SIZE
    assert 0 < pointer_map_bytes <= PAGE_SIZE
    database_copy.write_bytes(
        raw[header_offset : header_offset + PAGE_SIZE]
        + (raw[header_offset + PAGE_SIZE :] + bytes(PAGE_SIZE))[:PAGE_SIZE]
        + raw[2 * PAGE_SIZE : header_offset]
    )
    target_pages = header_offset // PAGE_SIZE

    with sqlite3.connect(database_copy) as db:
        items = db.execute(
            "SELECT id, parent FROM items WHERE name GLOB 'caption_*'"
        ).fetchall()
        caption_ids = [row[0] for row in items]
        assert caption_ids, "No caption items found"
        placeholders = ",".join("?" for _ in caption_ids)
        assert db.execute(
            f"SELECT COUNT(*) FROM items WHERE parent IN ({placeholders})",
            caption_ids,
        ).fetchone()[0] == 0, "Caption has child items"

        # Require a one-to-one mapping to generated SVGs before deleting anything.
        linked = db.execute(
            f"""SELECT ii.id, ii.image, im.format, im.source
                FROM items_images AS ii JOIN images AS im ON im.id = ii.image
                WHERE ii.id IN ({placeholders})""",
            caption_ids,
        ).fetchall()
        assert len(linked) == len(caption_ids), "Caption/image count mismatch"
        assert all(fmt == "SVG" and "/labels/caption_" in path.replace("\\", "/")
                   for _, _, fmt, path in linked), "Non-caption image matched"
        image_ids = [image_id for _, image_id, _, _ in linked]
        assert len(image_ids) == len(set(image_ids)), "Shared image record"
        note_count = db.execute("SELECT COUNT(*) FROM items_notes").fetchone()[0]

        # Delete the dependent item records, then their unshared SVG resources.
        with db:
            db.executemany("DELETE FROM items_images WHERE id = ?", ((i,) for i in caption_ids))
            db.executemany("DELETE FROM items WHERE id = ?", ((i,) for i in caption_ids))
            db.executemany("DELETE FROM images WHERE id = ?", ((i,) for i in image_ids))
        assert db.execute("SELECT COUNT(*) FROM items WHERE name GLOB 'caption_*'").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM items_notes").fetchone()[0] == note_count
        assert db.execute("SELECT COUNT(*) FROM images WHERE format = 'SVG'").fetchone()[0] == 0
        print(f"Removed {len(caption_ids)} captions; retained {note_count} notes")

        # Keep the page count fixed for the PureRef wrapper. PureRef drops this
        # temporary table automatically when it next saves the clean scene.
        db.execute("CREATE TABLE codex_padding (data BLOB)")
        db.execute("INSERT INTO codex_padding(data) VALUES (?)", (bytes(62_000),))
        db.commit()
        actual_pages = db.execute("PRAGMA page_count").fetchone()[0]
        assert actual_pages == target_pages, f"Page count changed: {actual_pages} != {target_pages}"

    edited = database_copy.read_bytes()
    assert len(edited) == header_offset

    # Restore the scene pages, header page, and partial pointer-map trailer.
    packed = bytearray(raw)
    packed[2 * PAGE_SIZE : header_offset] = edited[2 * PAGE_SIZE :]
    packed[header_offset : header_offset + PAGE_SIZE] = edited[:PAGE_SIZE]
    packed[header_offset + PAGE_SIZE :] = edited[PAGE_SIZE : PAGE_SIZE + pointer_map_bytes]
    packed[40:104] = hashlib.md5(packed[104:]).hexdigest().encode("utf-16-be")
    candidate.write_bytes(packed)
    print(f"Candidate: {candidate}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("database_copy", type=Path)
    args = parser.parse_args()
    remove_captions(args.source, args.candidate, args.database_copy)
