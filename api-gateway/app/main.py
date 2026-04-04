from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import AsyncClient, Timeout

from app.core.config import settings
from app.routes import api, docs_links, health, openapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One shared HTTP client keeps connections warm for better proxy performance.
    app.state.http_client = AsyncClient(
        timeout=Timeout(settings.request_timeout_seconds),
        follow_redirects=False,
    )
    yield
    await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    app.include_router(openapi.router)
    app.include_router(health.router)
    app.include_router(docs_links.router)
    app.include_router(api.router, prefix="/api/v1")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
