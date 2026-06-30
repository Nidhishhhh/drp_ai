from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from models.schemas import SearchResponse, DetectionResult
from utils.file_handler import save_upload, delete_file
from services.detector import detect_item
from services.embedder import get_image_embedding
from services.searcher import search_similar, index
import os

router = APIRouter()

@router.post("/search")
async def search(file: UploadFile = File(...)):
    print(f"[DEBUG] Received file: {file.filename}, type: {file.content_type}")
    
    image_path = await save_upload(file)
    print(f"[DEBUG] Saved to: {image_path}")
    
    try:
        # Step 1 — Run detection
        detection = detect_item(image_path)
        print(f"[DEBUG] Detection result: {detection}")
        
        # Step 2 — Get embedding from cropped image
        crop_path = detection.get("cropped_image_path")
        if crop_path and os.path.exists(crop_path):
            print(f"[DEBUG] Using crop: {crop_path}")
            embedding = get_image_embedding(crop_path)
        else:
            print(f"[DEBUG] No crop, using original: {image_path}")
            embedding = get_image_embedding(image_path)
        
        print(f"[DEBUG] Embedding generated, shape: {len(embedding)}")
        
        # Step 3 — Search similar items
        if index and index.ntotal > 0:
            print(f"[DEBUG] Index has {index.ntotal} items")
            similar = search_similar(embedding, top_k=10)
            print(f"[DEBUG] Found {len(similar)} similar items")
        else:
            print(f"[DEBUG] Index is empty or not loaded!")
            similar = []
        
        # Return response
        return {
            "detection": detection,
            "similar_items": similar,
            "message": f"Found {len(similar)} similar items"
        }
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
    finally:
        # Clean up original upload
        if os.path.exists(image_path):
            delete_file(image_path)