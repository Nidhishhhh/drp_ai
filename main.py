import os
import requests
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import init_db
import uvicorn
from fastapi.staticfiles import StaticFiles

# ==========================================
# AUTO-DOWNLOAD MISSING FILES (RUNS FIRST!)
# ==========================================
def download_file(url, dest_path):
    """Downloads a file if it does not exist."""
    if os.path.exists(dest_path):
        print(f"✅ File already exists: {dest_path}")
        return

    print(f"⬇️ Downloading {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Download complete: {dest_path}")
    except Exception as e:
        print(f"❌ ERROR downloading {dest_path}: {e}")
        raise e

# ==========================================
# 🔴 IMPORTANT: REPLACE THESE WITH YOUR DROPBOX DIRECT LINKS (must end with ?dl=1)
# ==========================================
MODEL_URL = "https://www.dropbox.com/scl/fi/li89vjj4f55osby0st4mv/drp_yolo.pt?rlkey=5ykdvszjdve33y43jr9wox1t3&st=xusg3uir&dl=1" 
INDEX_URL = "https://www.dropbox.com/scl/fi/ks8a0jxmusb2g6y7368st/drp.index?rlkey=9e1d1az3qkbmzgmfpmpge2bbo&st=8i1u9yfc&dl=1"
METADATA_URL = "https://www.dropbox.com/scl/fi/52c4mzfjpmdhbado64b1j/metadata.json?rlkey=4gdl634fqf3f9l4yndy2npalg&st=b84riyk8&dl=1"

# Download Model and Index files BEFORE importing routers
print("[drp.ai] Downloading required files...")
download_file(MODEL_URL, "models/drp_yolo.pt")
download_file(INDEX_URL, "data/index/drp.index")
download_file(METADATA_URL, "data/index/metadata.json")
print("[drp.ai] All files downloaded successfully! ✅")

# ==========================================
# NOW IMPORT ROUTERS (AFTER FILES ARE DOWNLOADED)
# ==========================================
from routers import search, auth

# ==========================================
# LIFESPAN (Runs on Startup)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[drp.ai] Initializing database...")
    await init_db()
    print("[drp.ai] App started ✅")
    yield
    print("[drp.ai] App shutting down")


app = FastAPI(
    title="drp.ai",
    description="AI-powered fashion visual search engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth")
app.mount("/products", StaticFiles(directory="data/products"), name="products")


@app.get("/")
async def root():
    return {"message": "drp.ai is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)