import torch
import clip
from PIL import Image

# Global cache for model and preprocess
_gender_model = None
_gender_preprocess = None
_device = None

def get_gender_model():
    """Lazy load CLIP model for gender detection"""
    global _gender_model, _gender_preprocess, _device
    if _gender_model is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _gender_model, _gender_preprocess = clip.load("ViT-B/32", device=_device)
        print(f"[drp.ai] Gender CLIP loaded on {_device}")
    return _gender_model, _gender_preprocess, _device

def detect_gender_from_image(image_path: str) -> dict:
    """
    Detect gender from clothing using CLIP zero-shot classification.
    Returns: {'gender': 'men'|'women'|'unisex', 'confidence': float}
    """
    model, preprocess, device = get_gender_model()
    
    # Load and preprocess image
    try:
        image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    except Exception as e:
        print(f"[drp.ai] Error loading image for gender detection: {e}")
        return {"gender": "unisex", "confidence": 0.0}
    
    # Define gender descriptors — more specific for clothing
    text_prompts = [
        "men's clothing, masculine style, male fashion",
        "women's clothing, feminine style, female fashion",
        "unisex clothing, androgynous style, gender neutral"
    ]
    
    text = clip.tokenize(text_prompts).to(device)
    
    with torch.no_grad():
        logits_per_image, _ = model(image, text)
        probs = logits_per_image.softmax(dim=-1)
    
    # Map to gender labels
    gender_labels = ["men", "women", "unisex"]
    best_idx = probs.argmax().item()
    confidence = float(probs[0][best_idx].item())
    
    return {
        "gender": gender_labels[best_idx],
        "confidence": round(confidence, 4)
    }