from pydantic import BaseModel
from typing import List, Optional

class DetectionResult(BaseModel):
    detected_item: str
    confidence: float
    bounding_box: List[float]
    cropped_image_path: str
    status: str

class SimilarItem(BaseModel):
    item_id: str
    score: float          # cosine similarity 0.0 - 1.0
    metadata: Optional[dict] = None

class SearchResponse(BaseModel):
    detection: DetectionResult
    similar_items: List[SimilarItem] = []
    message: Optional[str] = None