from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# `app/core/config.py` -> parents[2] == `api-gateway/`
_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _SERVICE_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "api-gateway"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Shared timeout used for proxy requests and health checks.
    request_timeout_seconds: float = 10.0

    # Downstream service base URLs (set in `.env` for each environment).
    user_service_url: str = "http://127.0.0.1:8001"
    product_service_url: str = "http://127.0.0.1:8002"
    order_service_url: str = "http://127.0.0.1:8003"
    payment_service_url: str = "http://127.0.0.1:8004"
    cart_service_url: str = "http://127.0.0.1:8005"
    review_service_url: str = "http://127.0.0.1:8006"
    notification_service_url: str = "http://127.0.0.1:8007"

    @property
    def service_map(self) -> dict[str, str]:
        # Keys match the first path segment after `/api/v1/`.
        return {
            "users": self.user_service_url,
            "products": self.product_service_url,
            "orders": self.order_service_url,
            "payments": self.payment_service_url,
            "cart": self.cart_service_url,
            "reviews": self.review_service_url,
            "notifications": self.notification_service_url,
        }


settings = Settings()
