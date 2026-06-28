from ultralytics import YOLO
import cv2
import os
import uuid

TEMP_DIR = "temp"

# Load model once at startup — never per request
model = YOLO("yolov8n.pt")  # nano model, fast on 4GB VRAM

FASHION_CLASSES = {
    "sneaker", "shoe", "boot", "sandal",
    "shirt", "t-shirt", "jacket", "coat",
    "pants", "jeans", "shorts", "skirt",
    "dress", "handbag", "backpack", "hat"
}

def detect_item(image_path: str) -> dict:
    results = model(image_path, verbose=False)
    
    best = None
    best_conf = 0.0

    for result in results:
        for box in result.boxes:
            label = model.names[int(box.cls)]
            conf = float(box.conf)

            if conf > best_conf:
                best_conf = conf
                best = {
                    "label": label,
                    "confidence": round(conf, 4),
                    "box": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                }

    if not best:
        return {
            "detected_item": "unknown",
            "confidence": 0.0,
            "bounding_box": [],
            "cropped_image_path": "",
            "status": "no_detection"
        }

    # Crop the detected item
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = [int(v) for v in best["box"]]
    cropped = img[y1:y2, x1:x2]

    crop_filename = f"crop_{uuid.uuid4().hex}.jpg"
    crop_path = os.path.join(TEMP_DIR, crop_filename)
    cv2.imwrite(crop_path, cropped)

    return {
        "detected_item": best["label"],
        "confidence": best["confidence"],
        "bounding_box": best["box"],
        "cropped_image_path": crop_path,
        "status": "success"
    }