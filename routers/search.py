from fastapi import APIRouter, UploadFile, File
from models.schemas import SearchResponse, DetectionResult
from utils.file_handler import save_upload, delete_file
from services.detector import detect_item

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search(file: UploadFile = File(...)):
    
    # Step 1 — Save uploaded image to temp/
    image_path = await save_upload(file)

    try:
        # Step 2 — Run YOLO detection
        detection = detect_item(image_path)

        # Step 3 — Build response
        return SearchResponse(
            detection=DetectionResult(**detection),
            message="Detection successful" if detection["status"] == "success" else "No item detected"
        )

    finally:
        # Step 4 — Always delete the original upload, even if something crashes
        delete_file(image_path)