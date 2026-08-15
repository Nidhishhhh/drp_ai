"""
drp.ai — services/gender_classifier.py
Detects gender (male/female) from a clothing image using a pretrained
HuggingFace ViT model: rizvandwiki/gender-classification

Loaded once at startup, runs on GPU if available.
Returns "male", "female", or "unknown".
"""

import torch
from PIL import Image
from transformers import ViTForImageClassification, ViTImageProcessor

MODEL_NAME = "rizvandwiki/gender-classification"

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[drp.ai] Loading gender classifier on {device}...")
try:
    processor = ViTImageProcessor.from_pretrained(MODEL_NAME)
    model = ViTForImageClassification.from_pretrained(MODEL_NAME).to(device)
    model.eval()
    print(f"[drp.ai] Gender classifier ready ✅")
    CLASSIFIER_LOADED = True
except Exception as e:
    print(f"[drp.ai] Gender classifier failed to load: {e}")
    CLASSIFIER_LOADED = False
    processor = None
    model = None


def detect_gender(image_path: str) -> str:
    """
    Returns "male", "female", or "unknown".
    Uses the full image (not just the crop) for better context.
    """
    if not CLASSIFIER_LOADED:
        return "unknown"

    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = logits.argmax(-1).item()
            label = model.config.id2label[predicted_class].lower()

        # Normalize label to male/female
        if "male" in label and "female" not in label:
            gender = "male"
        elif "female" in label:
            gender = "female"
        else:
            gender = "unknown"

        confidence = torch.softmax(logits, dim=-1).max().item()
        print(f"[drp.ai] Gender detected: {gender} ({confidence:.2%} confidence)")
        return gender

    except Exception as e:
        print(f"[drp.ai] Gender detection failed: {e}")
        return "unknown"