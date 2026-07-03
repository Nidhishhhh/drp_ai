"""
drp.ai — Phase 6
Migrates absolute image paths in metadata.json to portable relative paths.

Run this ONCE on your local PC — it rewrites metadata.json in place.
No dataset needed — it only touches the metadata file.

Before:
  "image_path": "C:\\Users\\prane\\Downloads\\archive\\DeepFashion2\\...\\train\\image\\052124.jpg"

After:
  "image_path": "train/image/052124.jpg"

This makes the index portable — paths resolve correctly on any machine
once you configure DATASET_BASE_PATH in config.py.
"""

import json
import re
import shutil
from pathlib import Path

META_PATH = Path("data/index/metadata.json")
BACKUP_PATH = Path("data/index/metadata.json.bak")

# Regex to extract the portable part: train/image/XXXXXX.jpg or validation/image/XXXXXX.jpg
PORTABLE_RE = re.compile(r"((?:train|validation|test)[/\\]image[/\\][^\"\\]+\.jpg)", re.IGNORECASE)


def migrate():
    if not META_PATH.exists():
        print(f"[drp.ai] ERROR: {META_PATH} not found — check the path and try again")
        return

    # Backup first
    shutil.copy2(META_PATH, BACKUP_PATH)
    print(f"[drp.ai] Backup saved to {BACKUP_PATH}")

    with open(META_PATH, "r") as f:
        metadata = json.load(f)

    total = len(metadata)
    migrated = 0
    already_portable = 0
    failed = 0

    for item_id, item in metadata.items():
        path = item.get("image_path", "")

        # Check if already portable (no drive letter or absolute path marker)
        if not Path(path).is_absolute() and not re.match(r"[A-Za-z]:\\", path):
            already_portable += 1
            continue

        match = PORTABLE_RE.search(path)
        if match:
            portable = match.group(1).replace("\\", "/")
            item["image_path"] = portable
            migrated += 1
        else:
            print(f"[drp.ai] Could not migrate item {item_id}: {path}")
            failed += 1

    with open(META_PATH, "w") as f:
        json.dump(metadata, f)

    print(f"""
[drp.ai] Migration complete ✅
  Total items    : {total}
  Migrated       : {migrated}
  Already portable: {already_portable}
  Failed         : {failed}

Portable paths now look like: train/image/052124.jpg
Configure DATASET_BASE_PATH in config.py to resolve them at query time.
""")


if __name__ == "__main__":
    migrate()