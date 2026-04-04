"""Convenience redirects to downstream Swagger docs for demos."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.core.config import settings

router = APIRouter(tags=["docs-links"])


def _service_docs_redirect(service_key: str) -> RedirectResponse:
    """
    Build a redirect response to a downstream service's `/docs` URL.

    Kept as a helper so each route stays tiny and easy to understand.
    """
    base = settings.service_map[service_key].rstrip("/")
    return RedirectResponse(url=f"{base}/docs", status_code=307)


@router.get("/docs/users", include_in_schema=False)
async def docs_users() -> RedirectResponse:
    return _service_docs_redirect("users")


@router.get("/docs/products", include_in_schema=False)
async def docs_products() -> RedirectResponse:
    return _service_docs_redirect("products")


@router.get("/docs/orders", include_in_schema=False)
async def docs_orders() -> RedirectResponse:
    return _service_docs_redirect("orders")


@router.get("/docs/payments", include_in_schema=False)
async def docs_payments() -> RedirectResponse:
    return _service_docs_redirect("payments")


@router.get("/docs/cart", include_in_schema=False)
async def docs_cart() -> RedirectResponse:
    return _service_docs_redirect("cart")


@router.get("/docs/reviews", include_in_schema=False)
async def docs_reviews() -> RedirectResponse:
    return _service_docs_redirect("reviews")


@router.get("/docs/notifications", include_in_schema=False)
async def docs_notifications() -> RedirectResponse:
    return _service_docs_redirect("notifications")
