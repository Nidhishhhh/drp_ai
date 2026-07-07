"""
drp.ai — routers/search.py
Async search pipeline using Celery.

POST /api/v1/search      — uploads image, returns task_id immediately
GET  /api/v1/results/{task_id} — poll for results
"""

from fastapi import APIRouter, UploadFile, File, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from utils.file_handler import save_upload
from worker.tasks import detect_and_search
from worker.celery_app import celery_app
from database.session import get_db
from database.models import SearchHistory

router = APIRouter()


@router.post("/search")
async def search(
    file: UploadFile = File(...),
    sort_by: str = Query(default="relevance", enum=["relevance", "price_asc", "price_desc"]),
    top_k: int = Query(default=10, ge=1, le=50),
):
    """
    Upload an image to search for similar fashion items.
    Returns a task_id immediately — poll /results/{task_id} for results.
    """
    image_path = await save_upload(file)

    # Fire off the Celery task — returns immediately
    task = detect_and_search.delay(
        image_path=image_path,
        sort_by=sort_by,
        top_k=top_k,
    )

    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Search started — poll /api/v1/results/{task_id} for results",
        "poll_url": f"/api/v1/results/{task.id}",
    }


@router.get("/results/{task_id}")
async def get_results(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Poll for search results using the task_id from /search.

    Returns:
        - status: "processing" | "complete" | "failed"
        - result: the search results (only when status is "complete")
    """
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        return {
            "task_id": task_id,
            "status": "processing",
            "step": "queued",
        }

    if task.state == "PROGRESS":
        return {
            "task_id": task_id,
            "status": "processing",
            "step": task.info.get("step", "working"),
        }

    if task.state == "SUCCESS":
        result = task.result

        # Save search history to DB
        try:
            detection = result.get("detection", {})
            history = SearchHistory(
                user_id=None,
                detected_item=detection.get("detected_item", "unknown"),
                confidence=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", []),
                results=[
                    {"item_id": s["item_id"], "score": s["score"]}
                    for s in result.get("similar_items", [])
                ],
                sort_by=result.get("sort_by", "relevance"),
            )
            db.add(history)
            await db.commit()
        except Exception as e:
            print(f"[WARNING] Failed to save search history: {e}")

        return {
            "task_id": task_id,
            "status": "complete",
            "result": result,
        }

    if task.state == "FAILURE":
        return JSONResponse(
            status_code=500,
            content={
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info),
            }
        )

    return {"task_id": task_id, "status": task.state}