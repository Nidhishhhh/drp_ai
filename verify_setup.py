"""
verify_setup.py - Phase 1 Verification Script
===============================================
Run this after completing Phase 1 setup.
It checks every dependency and prints a clear pass/fail.

Run with:
    python verify_setup.py

Every line should show [PASS]. If anything shows [FAIL],
fix that package before moving to Phase 2.
"""

import sys

# Track overall result
all_passed = True


def check(label: str, fn):
    """Runs a check function and prints pass/fail with version info."""
    global all_passed
    try:
        result = fn()
        print(f"  [PASS] {label}: {result}")
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        all_passed = False


def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


# ----------------------------------------------------------
# Python Version
# ----------------------------------------------------------
section("Python")

def check_python():
    v = sys.version_info
    assert v.major == 3 and v.minor == 10, f"Need Python 3.10, got {v.major}.{v.minor}"
    return f"{v.major}.{v.minor}.{v.micro}"

check("Python version (need 3.10.x)", check_python)


# ----------------------------------------------------------
# PyTorch & CUDA
# ----------------------------------------------------------
section("PyTorch & CUDA (most important)")

def check_torch():
    import torch
    return torch.__version__

def check_cuda_available():
    import torch
    assert torch.cuda.is_available(), "CUDA not available - check NVIDIA drivers"
    return f"CUDA {torch.version.cuda}"

def check_gpu_name():
    import torch
    name = torch.cuda.get_device_name(0)
    return name

def check_gpu_memory():
    import torch
    mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    return f"{mem:.1f} GB VRAM"

def check_cuda_tensor():
    import torch
    t = torch.tensor([1.0, 2.0]).cuda()
    return f"Tensor on {t.device} - GPU compute working"

check("PyTorch installed", check_torch)
check("CUDA available", check_cuda_available)
check("GPU detected", check_gpu_name)
check("GPU memory", check_gpu_memory)
check("GPU compute test", check_cuda_tensor)


# ----------------------------------------------------------
# Computer Vision
# ----------------------------------------------------------
section("Computer Vision")

def check_ultralytics():
    import ultralytics
    return ultralytics.__version__

def check_opencv():
    import cv2
    return cv2.__version__

def check_pillow():
    from PIL import Image
    import PIL
    return PIL.__version__

def check_numpy():
    import numpy as np
    return np.__version__

check("Ultralytics (YOLOv8)", check_ultralytics)
check("OpenCV (headless)", check_opencv)
check("Pillow (image loading)", check_pillow)
check("NumPy", check_numpy)


# ----------------------------------------------------------
# CLIP & FAISS
# ----------------------------------------------------------
section("AI Models")

def check_open_clip():
    import open_clip
    # Try calling list_models() to prove the package is healthy and initialized
    open_clip.list_models()
    return "installed and initialized successfully"



def check_faiss():
    import faiss
    # Try creating a basic index to confirm it works
    import numpy as np
    index = faiss.IndexFlatL2(128)
    vecs = np.random.random((10, 128)).astype("float32")
    index.add(vecs)
    D, I = index.search(vecs[:1], 5)
    return f"v{faiss.__version__} — search test passed (5 results returned)"

check("open-clip-torch (CLIP)", check_open_clip)
check("FAISS", check_faiss)


# ----------------------------------------------------------
# Web Framework
# ----------------------------------------------------------
section("Web Framework")

def check_fastapi():
    import fastapi
    return fastapi.__version__

def check_uvicorn():
    import uvicorn
    return uvicorn.__version__

def check_pydantic():
    import pydantic
    return pydantic.__version__

def check_multipart():
    import multipart
    return "installed"

def check_aiofiles():
    import aiofiles
    return "installed"

check("FastAPI", check_fastapi)
check("Uvicorn", check_uvicorn)
check("Pydantic v2", check_pydantic)
check("python-multipart (file uploads)", check_multipart)
check("aiofiles (async file I/O)", check_aiofiles)


# ----------------------------------------------------------
# Background Jobs
# ----------------------------------------------------------
section("Background Jobs (Phase 7)")

def check_celery():
    import celery
    return celery.__version__

def check_redis():
    import redis
    return redis.__version__

check("Celery", check_celery)
check("Redis client", check_redis)


# ----------------------------------------------------------
# Database
# ----------------------------------------------------------
section("Database (Phase 8)")

def check_sqlalchemy():
    import sqlalchemy
    return sqlalchemy.__version__

def check_alembic():
    import alembic
    return alembic.__version__

def check_asyncpg():
    import asyncpg
    return asyncpg.__version__

check("SQLAlchemy", check_sqlalchemy)
check("Alembic (migrations)", check_alembic)
check("asyncpg (async PostgreSQL)", check_asyncpg)


# ----------------------------------------------------------
# Auth
# ----------------------------------------------------------
section("Authentication (Phase 9)")

def check_jose():
    from jose import jwt
    return "python-jose installed"

def check_bcrypt():
    import bcrypt
    return bcrypt.__version__

def check_passlib():
    import passlib
    return passlib.__version__

check("python-jose (JWT)", check_jose)
check("bcrypt (password hashing)", check_bcrypt)
check("passlib", check_passlib)


# ----------------------------------------------------------
# Scraping
# ----------------------------------------------------------
section("Scraping (Phase 10)")

def check_selenium():
    import selenium
    return selenium.__version__

def check_bs4():
    import bs4
    return bs4.__version__

def check_webdriver_manager():
    import webdriver_manager
    return webdriver_manager.__version__

def check_undetected():
    import undetected_chromedriver
    return "installed"

check("Selenium", check_selenium)
check("BeautifulSoup4", check_bs4)
check("webdriver-manager", check_webdriver_manager)
check("undetected-chromedriver", check_undetected)


# ----------------------------------------------------------
# Data & Utils
# ----------------------------------------------------------
section("Data & Utilities")

def check_pandas():
    import pandas as pd
    return pd.__version__

def check_dotenv():
    import dotenv
    return "installed"

def check_boto3():
    import boto3
    return boto3.__version__

def check_structlog():
    import structlog
    return structlog.__version__

check("Pandas", check_pandas)
check("python-dotenv", check_dotenv)
check("boto3 (Cloudflare R2)", check_boto3)
check("structlog (logging)", check_structlog)


# ----------------------------------------------------------
# Project Config
# ----------------------------------------------------------
section("Project Config")

def check_config():
    from config import settings
    return f"Loaded — device will be: {settings.resolved_device}"

def check_dirs():
    from pathlib import Path
    dirs = [
        "app", "scraper", "models", "data/product_index",
        "data/product_catalog", "static/uploads", "templates",
        "tests", "logs"
    ]
    missing = [d for d in dirs if not Path(d).exists()]
    assert not missing, f"Missing directories: {missing}"
    return f"All {len(dirs)} directories present"

check("config.py loads correctly", check_config)
check("Project directories", check_dirs)


# ----------------------------------------------------------
# Final Result
# ----------------------------------------------------------
print(f"\n{'='*55}")
if all_passed:
    print("  ALL CHECKS PASSED - Phase 1 complete!")
    print("  You're ready to start Phase 2.")
else:
    print("  SOME CHECKS FAILED - fix the [FAIL] items above")
    print("  before moving to Phase 2.")
print(f"{'='*55}\n")
