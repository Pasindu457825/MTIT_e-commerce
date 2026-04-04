"""Custom OpenAPI endpoints for the API gateway."""

from fastapi import APIRouter, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.openapi_service import build_gateway_openapi

router = APIRouter(tags=["openapi"])


@router.get("/openapi.json", include_in_schema=False)
async def openapi_json(request: Request) -> JSONResponse:
    schema = await build_gateway_openapi(request.app)
    return JSONResponse(schema)


@router.get("/docs", include_in_schema=False)
async def swagger_docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="api-gateway - Swagger UI",
    )
