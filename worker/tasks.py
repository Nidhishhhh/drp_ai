"""
drp.ai — worker/tasks.py
Full pipeline with Google Lens visual search + Amazon + text search fallback.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import asyncio
from worker.celery_app import celery_app
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar, index
from services.visual_search import enrich_results_with_visual_search
from services.image_host import upload_image
from utils.color_detector import get_dominant_color
from utils.file_handler import delete_file


@celery_app.task(bind=True, name="drp.detect_and_search", max_retries=2)
def detect_and_search(self, image_path: str, sort_by: str = "relevance", top_k: int = 10) -> dict:
    crop_path = None

    try:
        # Step 1 — YOLO detection
        self.update_state(state="PROGRESS", meta={"step": "detecting"})
        detection = detect_item(image_path)
        crop_path = detection.pop("_cropped_image_path", None)
        detected_category = detection.get("detected_item", "unknown")

        # Step 2 — Gender detection
        self.update_state(state="PROGRESS", meta={"step": "detecting"})
        from services.gender_classifier import detect_gender
        gender = detect_gender(image_path)

        # Step 3 — Color detection
        color = ""
        if crop_path and os.path.exists(crop_path):
            color = get_dominant_color(crop_path)

        # Step 4 — Upload crop to imgbb for public URL
        self.update_state(state="PROGRESS", meta={"step": "embedding"})
        crop_public_url = ""
        if crop_path and os.path.exists(crop_path):
            crop_public_url = asyncio.run(upload_image(crop_path))

        # Step 5 — CLIP embedding
        if crop_path and os.path.exists(crop_path):
            embedding = get_image_embedding(crop_path)
        else:
            embedding = get_image_embedding(image_path)

        # Step 6 — FAISS search
        self.update_state(state="PROGRESS", meta={"step": "searching"})
        if index and index.ntotal > 0:
            fetch_k = max(top_k * 3, 30)
            similar = search_similar(embedding, top_k=fetch_k)
        else:
            similar = []

        # Step 7 — Sort
        if sort_by == "price_asc":
            similar.sort(key=lambda x: x["metadata"].get("price", float("inf")))
        elif sort_by == "price_desc":
            similar.sort(key=lambda x: x["metadata"].get("price", 0), reverse=True)

        similar = similar[:top_k]

        # Step 8 — Visual search enrichment (Lens + Amazon + fallback)
        self.update_state(state="PROGRESS", meta={"step": "enriching"})
        try:
            similar = asyncio.run(
                enrich_results_with_visual_search(
                    similar,
                    crop_public_url,
                    detected_category,
                    color=color,
                    gender=gender,
                )
            )
            print(f"[drp.ai] Pipeline complete: gender={gender} color={color} category={detected_category}")
        except Exception as e:
            print(f"[drp.ai] Enrichment failed (non-fatal): {e}")

        return {
            "detection": {**detection, "color": color, "gender": gender},
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
            size = os.path.getsize(crop_path)
            print(f"[drp.ai] Crop file size: {size / 1024:.1f} KB")