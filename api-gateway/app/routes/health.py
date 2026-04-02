from fastapi import APIRouter, Request
from httpx import AsyncClient

from app.core.config import settings
from app.services.health_service import check_all_services

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    # Gateway-level liveness (does not ping downstream services).
    return {"status": "ok", "service": settings.app_name}


@router.get("/health/services")
async def health_services(request: Request) -> dict:
    # Aggregate health across all downstream services for quick diagnostics.
    client: AsyncClient = request.app.state.http_client
    return await check_all_services(client)
