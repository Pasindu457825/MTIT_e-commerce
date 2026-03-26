from typing import Any

from fastapi import APIRouter, Request, Response

from app.core.config import settings
from app.services.proxy_service import forward_to_service

router = APIRouter()


@router.get("/services", summary="List configured downstream base URLs")
async def list_services() -> dict[str, Any]:
    # Useful for local debugging to confirm env-based service URLs.
    return {"services": settings.service_map}


@router.api_route(
    "/{service_key}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def forward_root(service_key: str, request: Request) -> Response:
    """Forward requests like `/api/v1/users` to the same path on the target service."""
    return await forward_to_service(service_key=service_key, tail_path="", request=request)


@router.api_route(
    "/{service_key}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def forward_nested(service_key: str, path: str, request: Request) -> Response:
    """Forward requests like `/api/v1/users/123` with the same suffix downstream."""
    return await forward_to_service(service_key=service_key, tail_path=path, request=request)
