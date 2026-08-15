"""
drp.ai — utils/color_detector.py
Extracts the dominant color from a cropped clothing image.
Uses k-means clustering on pixel values to find the most prominent color.
"""

import cv2
import numpy as np


# Map RGB ranges to color names
COLOR_NAMES = [
    ("red",     (150, 0, 0),   (255, 80, 80)),
    ("pink",    (200, 100, 130), (255, 200, 200)),
    ("orange",  (180, 80, 0),  (255, 160, 80)),
    ("yellow",  (180, 160, 0), (255, 255, 100)),
    ("green",   (0, 100, 0),   (100, 200, 100)),
    ("blue",    (0, 0, 100),   (100, 150, 255)),
    ("navy",    (0, 0, 50),    (50, 80, 130)),
    ("purple",  (80, 0, 100),  (180, 80, 200)),
    ("brown",   (80, 40, 0),   (160, 100, 60)),
    ("grey",    (100, 100, 100), (180, 180, 180)),
    ("white",   (200, 200, 200), (255, 255, 255)),
    ("black",   (0, 0, 0),     (60, 60, 60)),
    ("beige",   (180, 160, 120), (240, 220, 180)),
]


def get_dominant_color(image_path: str) -> str:
    """
    Returns the dominant color name of the clothing item in the image.
    Falls back to empty string if detection fails.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return ""

        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize for speed
        img = cv2.resize(img, (100, 100))

        # Reshape to list of pixels
        pixels = img.reshape(-1, 3).astype(np.float32)

        # Remove near-white background pixels (common in product photos)
        mask = ~(
            (pixels[:, 0] > 230) &
            (pixels[:, 1] > 230) &
            (pixels[:, 2] > 230)
        )
        pixels = pixels[mask]

        if len(pixels) < 10:
            return ""

        # K-means to find dominant colors
        k = 3
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS
        )

        # Find most common cluster
        counts = np.bincount(labels.flatten())
        dominant = centers[np.argmax(counts)].astype(int)
        r, g, b = int(dominant[0]), int(dominant[1]), int(dominant[2])

        # Match to color name
        best_match = ""
        best_distance = float("inf")

        for name, (r_min, g_min, b_min), (r_max, g_max, b_max) in COLOR_NAMES:
            r_center = (r_min + r_max) / 2
            g_center = (g_min + g_max) / 2
            b_center = (b_min + b_max) / 2
            distance = ((r - r_center) ** 2 + (g - g_center) ** 2 + (b - b_center) ** 2) ** 0.5
            if distance < best_distance:
                best_distance = distance
                best_match = name

        print(f"[drp.ai] Dominant color: {best_match} (RGB: {r},{g},{b})")
        return best_match

    except Exception as e:
        print(f"[drp.ai] Color detection failed: {e}")
        return ""