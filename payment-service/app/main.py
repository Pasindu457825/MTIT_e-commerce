"""
Application entry point: FastAPI factory, middleware, MongoDB lifecycle, and routers.

Run locally (port comes from settings / `.env`):
    uvicorn app.main:app --host 0.0.0.0 --port <PORT> --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_mongodb, disconnect_mongodb
from app.core.exceptions import register_exception_handlers
from app.core.indexes import ensure_payment_indexes
from app.routes import api, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.

    Startup: connect to MongoDB and run a ping (fails fast if misconfigured).
    Shutdown: close the Motor client.
    """
    try:
        await connect_mongodb(app)
        await ensure_payment_indexes(app.state.mongodb)
    except Exception:
        # Re-raise so Uvicorn logs a clear startup failure (bad URI, network, etc.).
        await disconnect_mongodb(app)
        raise
    yield
    await disconnect_mongodb(app)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        version=settings.api_version,
    )

    # Consistent JSON errors for validation, MongoDB, and unexpected exceptions.
    register_exception_handlers(app)

    # Allow browser frontends to call this API.
    # Browsers forbid `credentials` + wildcard `*` origins together — disable credentials for `*`.
    _origins = settings.cors_origin_list
    _credentials = "*" not in _origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # `/health` is outside the versioned API (common for probes).
    app.include_router(health.router)
    # Versioned API (e.g. `/api/v1/payments`).
    app.include_router(api.router, prefix=f"/api/{settings.api_version}")

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
