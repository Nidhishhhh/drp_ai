from pydantic import BaseModel
from typing import List, Optional

class DetectionResult(BaseModel):
    detected_item: str
    confidence: float
    bounding_box: List[float]
    cropped_image_path: str
    status: str

class SearchResponse(BaseModel):
    detection: DetectionResult
    message: Optional[str] = None