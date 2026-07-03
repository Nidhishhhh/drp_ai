"""
drp.ai — Phase 6
Adds new product images to the existing FAISS index without rebuilding.

Usage:
    # Add all images in data/products/ that aren't already indexed
    python scripts/add_product.py

    # Add a specific image
    python scripts/add_product.py --image data/products/my_shirt.jpg

    # Add all images in a subfolder
    python scripts/add_product.py --folder data/products/summer_2026/

Place new product images under data/products/ before running.
The script updates drp.index and metadata.json in place.
"""

import argparse
import json
import os
import sys
import torch
import clip
import faiss
import numpy as np
from pathlib import Path
from PIL import Image

INDEX_PATH = Path("data/index/drp.index")
META_PATH  = Path("data/index/metadata.json")
PRODUCTS_DIR = Path("data/products")
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_clip():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[drp.ai] Loading CLIP on {device}...")
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device


def embed(image_path: Path, model, preprocess, device) -> np.ndarray:
    img = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model.encode_image(img)
        emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy().astype("float32")


def load_index_and_meta():
    if not INDEX_PATH.exists():
        print(f"[drp.ai] ERROR: {INDEX_PATH} not found")
        sys.exit(1)
    if not META_PATH.exists():
        print(f"[drp.ai] ERROR: {META_PATH} not found")
        sys.exit(1)

    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "r") as f:
        metadata = json.load(f)

    print(f"[drp.ai] Loaded index with {index.ntotal} items")
    return index, metadata


def already_indexed(image_path: Path, metadata: dict) -> bool:
    """Check if this image is already in the index by portable path."""
    portable = image_path.as_posix()
    return any(v.get("image_path") == portable for v in metadata.values())


def add_images(image_paths: list[Path]):
    index, metadata = load_index_and_meta()
    model, preprocess, device = load_clip()

    added = 0
    skipped = 0

    for img_path in image_paths:
        if not img_path.exists():
            print(f"[drp.ai] Skipping — file not found: {img_path}")
            skipped += 1
            continue

        if img_path.suffix.lower() not in SUPPORTED_EXTS:
            print(f"[drp.ai] Skipping — unsupported format: {img_path.name}")
            skipped += 1
            continue

        # Portable path relative to project root
        try:
            portable = img_path.relative_to(Path(".")).as_posix()
        except ValueError:
            portable = img_path.as_posix()

        if already_indexed(Path(portable), metadata):
            print(f"[drp.ai] Already indexed — skipping: {img_path.name}")
            skipped += 1
            continue

        try:
            emb = embed(img_path, model, preprocess, device)
            index.add(emb)

            item_id = str(index.ntotal - 1)
            metadata[item_id] = {
                "image_path": portable,
                "category": "unknown",   # update manually or via API later
                "style": 0,
                "split": "products",
                "pair_id": "",
                "source": "custom",
            }

            print(f"[drp.ai] Added: {img_path.name} → id {item_id}")
            added += 1

        except Exception as e:
            print(f"[drp.ai] Failed to add {img_path.name} — {e}")
            skipped += 1

    if added > 0:
        # Save updated index and metadata
        faiss.write_index(index, str(INDEX_PATH))
        with open(META_PATH, "w") as f:
            json.dump(metadata, f)
        print(f"\n[drp.ai] ✅ Added {added} products — index now has {index.ntotal} items")
    else:
        print(f"\n[drp.ai] Nothing new to add — {skipped} skipped")


def collect_images(args) -> list[Path]:
    if args.image:
        return [Path(args.image)]

    if args.folder:
        folder = Path(args.folder)
        return [p for p in folder.rglob("*") if p.suffix.lower() in SUPPORTED_EXTS]

    # Default: all images in data/products/ not yet indexed
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    return [p for p in PRODUCTS_DIR.rglob("*") if p.suffix.lower() in SUPPORTED_EXTS]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add products to drp.ai index")
    parser.add_argument("--image",  type=str, help="Path to a single image to add")
    parser.add_argument("--folder", type=str, help="Path to a folder of images to add")
    args = parser.parse_args()

    images = collect_images(args)
    if not images:
        print(f"[drp.ai] No images found to add. Place images in {PRODUCTS_DIR} and try again.")
        sys.exit(0)

    print(f"[drp.ai] Found {len(images)} image(s) to process")
    add_images(images)