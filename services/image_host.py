import httpx
import base64
import os
from PIL import Image
import io

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "3ffece779b29f1bae2016c5e60176b22")
IMGBB_URL = "https://api.imgbb.com/1/upload"


async def upload_image(image_path: str) -> str:
    try:
        # Resize image to max 800px before uploading — reduces size, avoids 400 errors
        with Image.open(image_path) as img:
            img.thumbnail((800, 800))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                IMGBB_URL,
                data={
                    "key": IMGBB_API_KEY,
                    "image": image_data,
                    "expiration": 300,
                }
            )
            response.raise_for_status()
            data = response.json()

        url = data.get("data", {}).get("url", "")
        print(f"[drp.ai] Image uploaded to imgbb: {url}")
        return url

    except httpx.HTTPStatusError as e:
        print(f"[drp.ai] imgbb upload failed: {e}")
        print(f"[drp.ai] imgbb response body: {e.response.text}")
        return ""
    except Exception as e:
        print(f"[drp.ai] imgbb upload failed: {e}")
        return ""