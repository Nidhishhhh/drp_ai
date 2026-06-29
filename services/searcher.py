import faiss
import numpy as np
import json
import os

INDEX_DIR = "data/index"
INDEX_PATH = os.path.join(INDEX_DIR, "drp.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.json")

EMBEDDING_DIM = 512  # CLIP ViT-B/32 output size

os.makedirs(INDEX_DIR, exist_ok=True)

# Load or create FAISS index
if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
    print(f"[drp.ai] FAISS index loaded — {index.ntotal} items")
else:
    index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner Product = cosine sim on normalized vecs
    print("[drp.ai] FAISS index created fresh")

# Load or create metadata store
if os.path.exists(META_PATH):
    with open(META_PATH, "r") as f:
        metadata_store = json.load(f)
else:
    metadata_store = {}


def search_similar(embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Query FAISS for top_k most similar items.
    Returns list of {item_id, score, metadata}
    """
    if index.ntotal == 0:
        return []

    query = np.array([embedding], dtype="float32")
    scores, indices = index.search(query, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        item_id = str(idx)
        results.append({
            "item_id": item_id,
            "score": round(float(score), 4),
            "metadata": metadata_store.get(item_id, {})
        })

    return results


def add_item(embedding: list[float], metadata: dict = {}) -> str:
    """
    Add a new item to the FAISS index + metadata store.
    Returns the assigned item_id.
    """
    vector = np.array([embedding], dtype="float32")
    index.add(vector)

    item_id = str(index.ntotal - 1)
    metadata_store[item_id] = metadata

    # Persist both
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(metadata_store, f)

    print(f"[drp.ai] Item added — ID: {item_id}, total: {index.ntotal}")
    return item_id