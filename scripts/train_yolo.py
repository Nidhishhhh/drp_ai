"""
drp.ai — Phase 5
Fine-tunes YOLOv8n on DeepFashion2 for clothing detection.

Tuned for 3GB VRAM (RTX 3050 laptop):
  - small batch size
  - reduced image size (416 instead of 640)
  - mixed precision (AMP) on by default in ultralytics

Run from the project root:
    python scripts/train_yolo.py
"""

from ultralytics import YOLO
import torch

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[drp.ai] Training on: {device}")
    if device == "cuda":
        print(f"[drp.ai] GPU: {torch.cuda.get_device_properties(0).name} | "
              f"{torch.cuda.get_device_properties(0).total_memory // 1024**3} GB VRAM")

    # Start from pretrained COCO weights — much faster convergence than training from scratch
    model = YOLO("yolov8n.pt")

    results = model.train(
        data="data/yolo_dataset/data.yaml",
        epochs=50,
        imgsz=416,          # smaller than default 640 — saves VRAM
        batch=8,             # safe starting point for 3GB; lower to 4 if you hit OOM
        device=device,
        patience=10,          # early stop if val loss plateaus for 10 epochs
        project="runs/drp_yolo",
        name="clothing_detector",
        workers=2,            # fewer dataloader workers — keeps RAM/CPU usage modest
        cache=False,          # don't cache images in RAM (dataset is large)
        amp=True,             # mixed precision — saves VRAM, speeds up training
        val=True,
        plots=True,
    )

    print("\n[drp.ai] Training complete ✅")
    print(f"[drp.ai] Best weights saved to: runs/drp_yolo/clothing_detector/weights/best.pt")
    print("[drp.ai] Copy that file into your project (e.g. models/drp_yolo.pt) "
          "and update services/detector.py to load it.")