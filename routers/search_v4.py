from fastapi import APIRouter, UploadFile, File, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from utils.file_handler import save_upload, delete_file
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar, index
from database.session import get_db
from database.models import SearchHistory
import os

router = APIRouter()


@router.post("/search")
async def search(
    file: UploadFile = File(...),
    sort_by: str = Query(default="relevance", enum=["relevance", "price_asc", "price_desc"]),
    top_k: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
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
            fetch_k = max(top_k * 3, 30)
            similar = search_similar(embedding, top_k=fetch_k)
        else:
            similar = []

        # Step 4 — Sort results
        if sort_by == "price_asc":
            similar.sort(key=lambda x: x["metadata"].get("price", float("inf")))
        elif sort_by == "price_desc":
            similar.sort(key=lambda x: x["metadata"].get("price", 0), reverse=True)

        similar = similar[:top_k]

        # Step 5 — Save search history to database (anonymous for now, user_id added in Phase 9)
        try:
            history = SearchHistory(
                user_id=None,  # will be set after Phase 9 auth
                detected_item=detection.get("detected_item", "unknown"),
                confidence=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", []),
                results=[{"item_id": s["item_id"], "score": s["score"]} for s in similar],
                sort_by=sort_by,
            )
            db.add(history)
            await db.commit()
            print(f"[DEBUG] Search history saved — id: {history.id}")
        except Exception as db_err:
            print(f"[WARNING] Failed to save search history: {db_err}")
            # Don't fail the request if DB write fails

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