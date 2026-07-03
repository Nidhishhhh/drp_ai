"""
drp.ai — services/searcher.py
Loads the FAISS index and resolves portable image paths at query time.

Portable paths in metadata look like: train/image/052124.jpg
At query time they resolve to: <DATASET_BASE_PATH>/train/image/052124.jpg

Set DATASET_BASE_PATH in your .env or config.py to wherever DeepFashion2
lives on the current machine. Custom products added via add_product.py
use full relative paths (e.g. data/products/shirt.jpg) and don't need
the base path.
"""

import json
import os
import faiss
import numpy as np
from pathlib import Path

INDEX_PATH = Path("data/index/drp.index")
META_PATH  = Path("data/index/metadata.json")

# Base path for resolving DeepFashion2 dataset images.
# Set DATASET_BASE_PATH in your environment or .env file.
# e.g. "C:/Users/Nidhu/Downloads/archive/DeepFashion2/deepfashion2_original_images"
# Leave empty ("") if dataset images aren't available on this machine.
DATASET_BASE_PATH = os.getenv("DATASET_BASE_PATH", "")


def _resolve_path(portable_path: str) -> str:
    """
    Resolve a portable path to an absolute path for the current machine.
    - Custom products (data/products/...): returned as-is (relative to project root)
    - Dataset images (train/image/... or validation/image/...): prepend DATASET_BASE_PATH
    """
    if portable_path.startswith("data/products/") or portable_path.startswith("data\\products\\"):
        return portable_path

    if DATASET_BASE_PATH:
        return str(Path(DATASET_BASE_PATH) / portable_path)

    # No base path configured — return portable path as-is
    return portable_path


# ── Load index ────────────────────────────────────────────────────────────────
index = None
metadata = {}

if INDEX_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    print(f"[drp.ai] FAISS index loaded — {index.ntotal} items")
else:
    print(f"[drp.ai] WARNING: Index not found at {INDEX_PATH}")

if META_PATH.exists():
    with open(META_PATH, "r") as f:
        metadata = json.load(f)
    print(f"[drp.ai] Metadata loaded — {len(metadata)} entries")
else:
    print(f"[drp.ai] WARNING: Metadata not found at {META_PATH}")


def search_similar(embedding: list, top_k: int = 10) -> list:
    if index is None or index.ntotal == 0:
        return []

    query = np.array([embedding], dtype="float32")
    # Normalize for cosine similarity
    faiss.normalize_L2(query)

    scores, indices = index.search(query, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        item_id = str(idx)
        item_meta = metadata.get(item_id, {})

        # Resolve portable path to absolute path for the current machine
        portable = item_meta.get("image_path", "")
        resolved = _resolve_path(portable)

        results.append({
            "item_id": item_id,
            "score": round(float(score), 4),
            "metadata": {
                **item_meta,
                "image_path": resolved,
            }
        })

    return results