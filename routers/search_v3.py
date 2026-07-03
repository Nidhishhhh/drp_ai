from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from utils.file_handler import save_upload, delete_file
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar, index
import os

router = APIRouter()

@router.post("/search")
async def search(
    file: UploadFile = File(...),
    sort_by: str = Query(default="relevance", enum=["relevance", "price_asc", "price_desc"]),
    top_k: int = Query(default=10, ge=1, le=50),
):
    """
    Search for visually similar fashion items.

    - **sort_by**: `relevance` (default) | `price_asc` (cheapest first) | `price_desc` (most expensive first)
    - **top_k**: number of results to return (1-50, default 10)
    """
    print(f"[DEBUG] Received file: {file.filename}, sort_by={sort_by}, top_k={top_k}")

    image_path = await save_upload(file)
    crop_path = None

    try:
        # Step 1 — Detect clothing item
        detection = detect_item(image_path)
        crop_path = detection.pop("_cropped_image_path", None)

        # Step 2 — Embed cropped or original image
        if crop_path and os.path.exists(crop_path):
            embedding = get_image_embedding(crop_path)
        else:
            embedding = get_image_embedding(image_path)

        # Step 3 — Search similar items
        if index and index.ntotal > 0:
            # Fetch more than needed so sorting has enough to work with
            fetch_k = max(top_k * 3, 30)
            similar = search_similar(embedding, top_k=fetch_k)
        else:
            similar = []

        # Step 4 — Sort results
        if sort_by == "price_asc":
            similar.sort(key=lambda x: x["metadata"].get("price", float("inf")))
        elif sort_by == "price_desc":
            similar.sort(key=lambda x: x["metadata"].get("price", 0), reverse=True)
        # "relevance" keeps FAISS order (highest similarity score first)

        # Trim to requested top_k
        similar = similar[:top_k]

        return {
            "detection": detection,
            "similar_items": similar,
            "sort_by": sort_by,
            "message": f"Found {len(similar)} similar items"
        }

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if os.path.exists(image_path):
            delete_file(image_path)
        if crop_path and os.path.exists(crop_path):
            delete_file(crop_path)