from fastapi import APIRouter, UploadFile, File
from models.schemas import SearchResponse, DetectionResult, SimilarItem
from utils.file_handler import save_upload, delete_file
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search(file: UploadFile = File(...)):

    # Step 1 — Save uploaded image to temp/
    image_path = await save_upload(file)

    try:
        # Step 2 — Run YOLO detection
        detection = detect_item(image_path)

        similar_items = []

        if detection["status"] == "success":
            crop_path = detection["cropped_image_path"]

            # Step 3 — Generate CLIP embedding from cropped image
            embedding = get_image_embedding(crop_path)

            # Step 4 — Search FAISS for similar items
            raw_results = search_similar(embedding, top_k=5)
            similar_items = [SimilarItem(**r) for r in raw_results]

            # Step 5 — Clean up crop
            delete_file(crop_path)

        return SearchResponse(
            detection=DetectionResult(**detection),
            similar_items=similar_items,
            message="Search complete" if detection["status"] == "success" else "No item detected"
        )

    finally:
        # Always delete original upload
        delete_file(image_path)