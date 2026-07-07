"""
drp.ai — worker/tasks.py
Celery tasks for the full async search pipeline:
  1. detect_and_embed — runs YOLO + CLIP on uploaded image
  2. search_index     — queries FAISS with the embedding
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from worker.celery_app import celery_app
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar, index
from utils.file_handler import delete_file


@celery_app.task(bind=True, name="drp.detect_and_search", max_retries=2)
def detect_and_search(self, image_path: str, sort_by: str = "relevance", top_k: int = 10) -> dict:
    """
    Full async pipeline: YOLO detection → CLIP embedding → FAISS search.
    """
    crop_path = None

    try:
        # Step 1 — YOLO detection
        self.update_state(state="PROGRESS", meta={"step": "detecting"})
        detection = detect_item(image_path)
        crop_path = detection.pop("_cropped_image_path", None)

        # Step 2 — CLIP embedding
        self.update_state(state="PROGRESS", meta={"step": "embedding"})
        if crop_path and os.path.exists(crop_path):
            embedding = get_image_embedding(crop_path)
        else:
            embedding = get_image_embedding(image_path)

        # Step 3 — FAISS search
        self.update_state(state="PROGRESS", meta={"step": "searching"})
        if index and index.ntotal > 0:
            fetch_k = max(top_k * 3, 30)
            similar = search_similar(embedding, top_k=fetch_k)
        else:
            similar = []

        # Step 4 — Sort
        if sort_by == "price_asc":
            similar.sort(key=lambda x: x["metadata"].get("price", float("inf")))
        elif sort_by == "price_desc":
            similar.sort(key=lambda x: x["metadata"].get("price", 0), reverse=True)

        similar = similar[:top_k]

        return {
            "detection": detection,
            "similar_items": similar,
            "sort_by": sort_by,
            "message": f"Found {len(similar)} similar items",
            "status": "complete",
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2)

    finally:
        if image_path and os.path.exists(image_path):
            delete_file(image_path)
        if crop_path and os.path.exists(crop_path):
            delete_file(crop_path)