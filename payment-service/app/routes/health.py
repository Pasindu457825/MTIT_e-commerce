"""
Liveness / readiness style endpoint for orchestrators and quick manual checks.

Note: MongoDB is validated on application *startup* (see `app.main.lifespan`).
This route stays cheap so load balancers can call it often.
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a simple OK payload identifying this service."""
    return {"status": "ok", "service": settings.app_name}
