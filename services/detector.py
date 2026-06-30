from ultralytics import YOLO
import cv2
import os
import uuid

TEMP_DIR = "temp"
model = YOLO("yolov8n.pt")

def detect_item(image_path: str) -> dict:
    print(f"[DEBUG] Running YOLO on: {image_path}")

    try:
        results = model(image_path, verbose=False)
        print(f"[DEBUG] YOLO results: {len(results)} detections")

        detections = results[0].boxes

        if detections is None or len(detections) == 0:
            print("[DEBUG] No objects detected")
            return {
                "detected_item": "none",
                "confidence": 0.0,
                "bounding_box": [],
                "cropped_image_path": "",
                "status": "no_detection"
            }

        # Pick the detection with highest confidence
        best_idx = detections.conf.argmax().item()
        confidence = float(detections.conf[best_idx])
        class_id = int(detections.cls[best_idx])
        class_name = model.names[class_id]
        bbox = detections.xyxy[best_idx].tolist()  # [x1, y1, x2, y2]

        print(f"[DEBUG] Best detection: {class_name} ({confidence:.2f}) at {bbox}")

        # Crop the image using the bounding box
        img = cv2.imread(image_path)
        x1, y1, x2, y2 = [int(v) for v in bbox]

        # Add small padding, clamp to image bounds
        pad = 10
        h, w = img.shape[:2]
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w, x2 + pad)
        y2 = min(h, y2 + pad)

        cropped = img[y1:y2, x1:x2]

        os.makedirs(TEMP_DIR, exist_ok=True)
        crop_filename = f"crop_{uuid.uuid4().hex}.jpg"
        crop_path = os.path.join(TEMP_DIR, crop_filename)
        cv2.imwrite(crop_path, cropped)

        print(f"[DEBUG] Cropped and saved to: {crop_path}")

        return {
            "detected_item": class_name,
            "confidence": round(confidence, 4),
            "bounding_box": bbox,
            "cropped_image_path": crop_path,
            "status": "success"
        }

    except Exception as e:
        print(f"[ERROR] YOLO failed: {e}")
        return {
            "detected_item": "unknown",
            "confidence": 0,
            "bounding_box": [],
            "cropped_image_path": "",
            "status": "error"
        }