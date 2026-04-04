"""
Application settings loaded from environment variables and optional `.env` file.

The `.env` file is resolved from this **service root** (`review-service/`), not the process
current working directory, so `uvicorn` can be launched from the repo root or this folder.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# `app/core/config.py` → parents[2] == `review-service/`
_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _SERVICE_ROOT / ".env"


class Settings(BaseSettings):
    """Central configuration — all values can be overridden via environment or `.env`."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Service identity & bind (see APP_* in `.env.example`) ---
    app_name: str = "review-service"
    app_host: str = "0.0.0.0"
    app_port: int = 8006
    debug: bool = False
    api_version: str = "v1"

    # --- Downstream integration (product-service validation) ---
    validate_product_on_create: bool = False
    product_service_url: str = "http://127.0.0.1:8002"
    product_service_timeout_seconds: float = 2.0

    # --- MongoDB (Motor; MONGODB_URL and DATABASE_NAME in `.env`) ---
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "review_db"

    # --- Collections (fixed name for this service) ---
    reviews_collection: str = "reviews"

    # --- CORS ---
    # Comma-separated list, e.g. "http://localhost:3000,http://127.0.0.1:3000"
    # Use "*" to allow any origin (fine for local dev; avoid in production with credentials).
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse `cors_origins` into a list for Starlette's CORSMiddleware."""
        parts = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return parts if parts else ["*"]

    @field_validator("database_name")
    @classmethod
    def db_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_NAME must be non-empty")
        return v.strip()

    @field_validator("product_service_timeout_seconds")
    @classmethod
    def product_timeout_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("PRODUCT_SERVICE_TIMEOUT_SECONDS must be > 0")
        return v


settings = Settings()
