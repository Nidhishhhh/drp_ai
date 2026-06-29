import torch
import clip
from PIL import Image

# Load CLIP model once at startup — never per request
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

print(f"[drp.ai] CLIP loaded on {device}")

def get_image_embedding(image_path: str) -> list[float]:
    """
    Takes a cropped image path, returns a 512-dim embedding vector.
    """
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)

    with torch.no_grad():
        embedding = model.encode_image(image)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # normalize

    return embedding.cpu().numpy().flatten().tolist()