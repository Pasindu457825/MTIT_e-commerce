"""
Central exception handlers so API errors are returned as consistent JSON.

Beginner tip: raise `HTTPException` in routes for expected errors (404, 403, â€¦).
Unexpected errors fall through to the generic handler below.
"""

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return 422 with readable validation details (body/query/path parameters)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed â€” check `detail` for field errors.",
        },
    )


async def pymongo_exception_handler(request: Request, exc: PyMongoError) -> JSONResponse:
    """
    MongoDB/driver errors become 503 so clients know to retry.

    In `debug` mode we include the raw message to speed up local troubleshooting.
    """
    payload: dict = {
        "detail": "Database error",
        "type": "mongodb",
    }
    if settings.debug:
        payload["detail"] = str(exc)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler for anything not caught elsewhere.

    Never leak stack traces or internal messages when `debug` is False.
    """
    payload: dict = {
        "detail": "Internal server error",
        "type": "unhandled",
    }
    if settings.debug:
        payload["detail"] = str(exc)
        payload["exception_type"] = type(exc).__name__
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire handlers onto the FastAPI instance."""
    # Preserve normal 404/401/403 behaviour from `HTTPException` in routes.
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PyMongoError, pymongo_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
