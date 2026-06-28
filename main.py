"""
main.py - Application Entry Point
===================================
This is the file you run to start the server.
It creates the FastAPI app instance and will wire
up all routes as we build each phase.

Run with:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging

from config import settings


# ----------------------------------------------------------
# Logging setup
# Basic for now - upgraded to structured JSON in Phase 13
# ----------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Lifespan - runs on startup and shutdown
# This is where we'll load models into memory (Phase 3, 5)
# so they're ready before the first request comes in
# ----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Running on device: {settings.resolved_device}")

    # Ensure upload directory exists
    settings.upload_dir_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.upload_dir_path}")

    # Phase 3: YOLO model will be loaded here
    # Phase 5: CLIP model will be loaded here
    # Phase 6: FAISS index will be loaded here

    yield  # App runs here

    # SHUTDOWN
    logger.info("Shutting down Fashion Search...")
    # Phase 3: YOLO cleanup here
    # Phase 5: CLIP cleanup here


# ----------------------------------------------------------
# FastAPI App Instance
# ----------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered fashion visual search engine",
    debug=settings.debug,
    lifespan=lifespan,
    # Disable docs in production (enable in debug only)
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ----------------------------------------------------------
# Static Files & Templates
# ----------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ----------------------------------------------------------
# Health Check Endpoints
# These are used by deployment platforms to know if app is alive
# ----------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check - returns 200 if app is running."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "device": settings.resolved_device,
    }


@app.get("/ready", tags=["System"])
async def readiness_check():
    """
    Readiness check - returns 200 only when all systems are ready.
    Will be expanded in Phase 3 to check if models are loaded.
    """
    return {
        "status": "ready",
        "models_loaded": False,  # Will be True after Phase 3
        "index_loaded": False,   # Will be True after Phase 6
    }


# ----------------------------------------------------------
# Routes (added as we build each phase)
# ----------------------------------------------------------
# Phase 2:  from app.routes import router; app.include_router(router)
# Phase 9:  from app.auth import auth_router; app.include_router(auth_router)
