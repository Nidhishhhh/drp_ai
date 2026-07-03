"""
drp.ai — Phase 5
Converts DeepFashion2 JSON annotations into YOLO label format.

DeepFashion2 bounding_box format: [x1, y1, x2, y2] in pixel coordinates.
YOLO label format (per line): class_id x_center y_center width height
  — all four values normalized to 0-1 relative to image width/height.

Run this once per split (train, validation) before training.
"""

import json
import os
from pathlib import Path
from PIL import Image

# ---- CONFIG — adjust these two paths if needed ----
SOURCE_DIR = Path("data/products")          # has train/ and validation/ subfolders
OUTPUT_DIR = Path("data/yolo_dataset")       # will be created
SPLITS = ["train", "validation"]

# DeepFashion2 category_id -> name (official 13 categories, ids start at 1)
CATEGORY_MAP = {
    1: "short_sleeve_top",
    2: "long_sleeve_top",
    3: "short_sleeve_outwear",
    4: "long_sleeve_outwear",
    5: "vest",
    6: "sling",
    7: "shorts",
    8: "trousers",
    9: "skirt",
    10: "short_sleeve_dress",
    11: "long_sleeve_dress",
    12: "vest_dress",
    13: "sling_dress",
}
# YOLO class ids must be 0-indexed
CATEGORY_TO_YOLO_ID = {cat_id: idx for idx, cat_id in enumerate(sorted(CATEGORY_MAP))}


def convert_split(split: str):
    image_dir = SOURCE_DIR / split / "image"
    anno_dir = SOURCE_DIR / split / "annos"

    # YOLO expects val images under "val", DeepFashion2 calls it "validation"
    yolo_split = "val" if split == "validation" else split

    out_image_dir = OUTPUT_DIR / "images" / yolo_split
    out_label_dir = OUTPUT_DIR / "labels" / yolo_split
    out_image_dir.mkdir(parents=True, exist_ok=True)
    out_label_dir.mkdir(parents=True, exist_ok=True)

    if not image_dir.exists():
        print(f"[drp.ai] Skipping {split} — {image_dir} not found")
        return 0, 0

    image_paths = list(image_dir.glob("*.jpg"))
    print(f"[drp.ai] {split} — {len(image_paths)} images found")

    converted = 0
    skipped = 0

    for i, img_path in enumerate(image_paths):
        anno_path = anno_dir / (img_path.stem + ".json")
        if not anno_path.exists():
            skipped += 1
            continue

        try:
            with open(anno_path, "r") as f:
                anno = json.load(f)

            with Image.open(img_path) as im:
                img_w, img_h = im.size

            items = {k: v for k, v in anno.items() if k.startswith("item")}
            lines = []

            for item_data in items.values():
                bbox = item_data.get("bounding_box")
                category_id = item_data.get("category_id")
                if not bbox or category_id not in CATEGORY_TO_YOLO_ID:
                    continue

                x1, y1, x2, y2 = bbox
                # Clamp to image bounds
                x1, x2 = max(0, x1), min(img_w, x2)
                y1, y2 = max(0, y1), min(img_h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue

                x_center = ((x1 + x2) / 2) / img_w
                y_center = ((y1 + y2) / 2) / img_h
                box_w = (x2 - x1) / img_w
                box_h = (y2 - y1) / img_h

                yolo_class = CATEGORY_TO_YOLO_ID[category_id]
                lines.append(f"{yolo_class} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}")

            if not lines:
                skipped += 1
                continue

            # Write label file
            label_path = out_label_dir / (img_path.stem + ".txt")
            with open(label_path, "w") as f:
                f.write("\n".join(lines))

            # Symlink (or copy on Windows) image into YOLO dataset folder
            out_img_path = out_image_dir / img_path.name
            if not out_img_path.exists():
                try:
                    os.symlink(img_path.resolve(), out_img_path)
                except OSError:
                    # Windows often needs admin rights for symlinks — fall back to copy
                    import shutil
                    shutil.copy2(img_path, out_img_path)

            converted += 1

            if (i + 1) % 1000 == 0:
                print(f"[drp.ai] {split}: {i + 1}/{len(image_paths)} processed — {converted} converted")

        except Exception as e:
            print(f"[drp.ai] Skipped {img_path.name} — {e}")
            skipped += 1

    return converted, skipped


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_converted = 0
    total_skipped = 0

    for split in SPLITS:
        c, s = convert_split(split)
        total_converted += c
        total_skipped += s

    print(f"\n[drp.ai] Conversion complete — {total_converted} converted, {total_skipped} skipped ✅")
    print(f"[drp.ai] YOLO dataset ready at: {OUTPUT_DIR.resolve()}")