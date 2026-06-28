import os
# Fix OpenMP runtime collision on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pathlib import Path
from dotenv import load_dotenv
# ... rest of your config.py code


"""
config.py - Central configuration for Fashion Search
=====================================================
All settings live here. Every other module imports from this file.
Never hardcode values anywhere else in the project.

Uses pydantic-settings which:
- Reads from .env file automatically
- Validates types (e.g. PORT must be an integer)
- Gives clear errors if required variables are missing
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import torch


# Project root directory (the folder containing this file)
ROOT_DIR = Path(__file__).parent


class Settings(BaseSettings):
    """
    All configuration values for the application.
    Values are loaded from .env file automatically.
    If a value has a default, it's optional in .env.
    If no default, it MUST be in .env or the app won't start.
    """

    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,      # APP_NAME and app_name both work
        extra="ignore",            # Ignore extra vars in .env
    )

    # ----------------------------------------------------------
    # App Settings
    # ----------------------------------------------------------
    app_name: str = "drp.ai"
    app_version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "change-this-in-production"

    # ----------------------------------------------------------
    # Server
    # ----------------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 8000

    # ----------------------------------------------------------
    # File Upload
    # ----------------------------------------------------------
    upload_dir: str = "static/uploads"
    max_file_size_mb: int = 5
    allowed_extensions: str = "jpg,jpeg,png,webp"

    # ----------------------------------------------------------
    # AI Models
    # ----------------------------------------------------------
    yolo_model_path: str = "models/yolov8n.pt"
    clip_model_name: str = "ViT-B/32"

    # Device auto-detection:
    # - Uses "cuda" if NVIDIA GPU is available
    # - Falls back to "cpu" if not
    # - Can be overridden in .env with DEVICE=cpu for testing
    device: str = "auto"

    # ----------------------------------------------------------
    # FAISS / Search
    # ----------------------------------------------------------
    faiss_index_path: str = "data/product_index/fashion.index"
    product_catalog_path: str = "data/product_catalog/products.json"
    top_k_results: int = 20

    # ----------------------------------------------------------
    # Database (Phase 8)
    # ----------------------------------------------------------
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/fashion_search"
    database_url_sync: str = "postgresql://user:password@localhost:5432/fashion_search"

    # ----------------------------------------------------------
    # Redis / Celery (Phase 7)
    # ----------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ----------------------------------------------------------
    # JWT Auth (Phase 9)
    # ----------------------------------------------------------
    jwt_secret_key: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # ----------------------------------------------------------
    # Cloudflare R2 (Phase 11)
    # ----------------------------------------------------------
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "fashion-search-uploads"
    r2_public_url: str = ""

    # ----------------------------------------------------------
    # Sentry (Phase 13)
    # ----------------------------------------------------------
    sentry_dsn: str = ""

    # ----------------------------------------------------------
    # Scraping (Phase 10)
    # ----------------------------------------------------------
    scrape_cache_ttl_hours: int = 6
    max_scrape_retries: int = 3
    scrape_delay_seconds: int = 2

    # ----------------------------------------------------------
    # Computed Properties (not from .env)
    # ----------------------------------------------------------

    @property
    def resolved_device(self) -> str:
        """
        Returns the actual device to use.
        If DEVICE=auto (default), checks if CUDA is available.
        This is called at runtime, not at import time.
        """
        if self.device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.device

    @property
    def allowed_extensions_set(self) -> set:
        """
        Converts the comma-separated string from .env
        into a Python set for fast lookup.
        e.g. "jpg,jpeg,png" -> {"jpg", "jpeg", "png"}
        """
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}

    @property
    def max_file_size_bytes(self) -> int:
        """Converts MB setting to bytes for file size checks."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def upload_dir_path(self) -> Path:
        """Returns the upload directory as a Path object."""
        return ROOT_DIR / self.upload_dir

    @property
    def faiss_index_path_full(self) -> Path:
        """Returns the FAISS index path as a Path object."""
        return ROOT_DIR / self.faiss_index_path

    @property
    def product_catalog_path_full(self) -> Path:
        """Returns the product catalog path as a Path object."""
        return ROOT_DIR / self.product_catalog_path


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    @lru_cache means this function only runs ONCE no matter
    how many times it's called across the entire application.
    This is important because loading settings reads from disk
    and we don't want to do that on every single request.

    Usage in other files:
        from config import get_settings
        settings = get_settings()
        print(settings.app_name)
    """
    return Settings()


# Module-level convenience - import this directly
# from config import settings
settings = get_settings()
