"""Proxy helpers used by route handlers."""

from __future__ import annotations

from fastapi import HTTPException, Request, Response, status
from httpx import AsyncClient, RequestError, Response as HttpxResponse, TimeoutException

from app.core.config import settings

# Hop-by-hop headers should not be forwarded by proxies.
_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _build_upstream_url(service_key: str, tail_path: str, query: str) -> str:
    base = settings.service_map.get(service_key)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown service prefix: {service_key}",
        )

    # Preserve the same API prefix on downstream services.
    # /api/v1/users           -> {user_service}/api/v1/users
    # /api/v1/users/abc       -> {user_service}/api/v1/users/abc
    normalized_tail = tail_path.strip("/")
    rel = service_key if not normalized_tail else f"{service_key}/{normalized_tail}"
    upstream = f"{base.rstrip('/')}/api/v1/{rel}"
    if query:
        upstream = f"{upstream}?{query}"
    return upstream


def _filtered_request_headers(request: Request) -> dict[str, str]:
    return {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }


_SAFE_RESPONSE_HEADERS = {
    "content-type",
    "location",
    "cache-control",
    "etag",
    "last-modified",
    "vary",
}


def _apply_response_headers(response: Response, upstream: HttpxResponse) -> None:
    """
    Copy a safe subset of upstream headers to the gateway response.

    We intentionally avoid forwarding hop-by-hop headers and `content-encoding`/`content-length`
    to prevent mismatches after httpx reads/decompresses response content.
    """
    for key, value in upstream.headers.items():
        key_l = key.lower()
        if key_l in _SAFE_RESPONSE_HEADERS and key_l not in _HOP_BY_HOP_HEADERS:
            response.headers[key] = value

    # Preserve all Set-Cookie headers (can appear multiple times).
    for cookie_value in upstream.headers.get_list("set-cookie"):
        response.headers.append("set-cookie", cookie_value)


async def forward_to_service(
    *,
    service_key: str,
    tail_path: str,
    request: Request,
) -> Response:
    """
    Reverse-proxy the current request to the target downstream service.

    Keeps method, query string, and body unchanged.
    """
    url = _build_upstream_url(service_key, tail_path, request.url.query)
    client: AsyncClient = request.app.state.http_client

    # Read body for every method; empty payloads become b"".
    body = await request.body()

    try:
        upstream = await client.request(
            method=request.method,
            url=url,
            headers=_filtered_request_headers(request),
            content=body,
        )
    except TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                f"Upstream timeout from '{service_key}' service "
                f"(>{settings.request_timeout_seconds}s)."
            ),
        ) from exc
    except RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach '{service_key}' service: {exc!s}",
        ) from exc

    response = Response(
        content=upstream.content,
        status_code=upstream.status_code,
    )
    _apply_response_headers(response, upstream)
    return response
