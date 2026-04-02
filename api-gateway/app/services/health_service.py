"""Downstream health aggregation helpers."""

from __future__ import annotations

import asyncio

from httpx import AsyncClient, RequestError, TimeoutException

from app.core.config import settings


async def check_service_health(client: AsyncClient, service_key: str, base_url: str) -> dict:
    """Check one downstream /health endpoint and return a compact status payload."""
    url = f"{base_url.rstrip('/')}/health"
    try:
        resp = await client.get(url)
        ok = 200 <= resp.status_code < 300
        payload: dict = {
            "service": service_key,
            "url": base_url,
            "status": "ok" if ok else "degraded",
            "status_code": resp.status_code,
        }
        # Helpful while learning: include JSON body if upstream returned one.
        if "application/json" in resp.headers.get("content-type", ""):
            try:
                payload["body"] = resp.json()
            except Exception:
                payload["body"] = resp.text[:200]
        return payload
    except TimeoutException:
        return {
            "service": service_key,
            "url": base_url,
            "status": "timeout",
            "status_code": None,
        }
    except RequestError as exc:
        return {
            "service": service_key,
            "url": base_url,
            "status": "unreachable",
            "status_code": None,
            "error": str(exc),
        }


async def check_all_services(client: AsyncClient) -> dict:
    """Run all downstream health checks and summarize a gateway-level status."""
    checks = await asyncio.gather(
        *[
            check_service_health(client, service_key, base_url)
            for service_key, base_url in settings.service_map.items()
        ]
    )
    all_ok = all(x["status"] == "ok" for x in checks)
    return {
        "status": "ok" if all_ok else "degraded",
        "gateway": settings.app_name,
        "services": checks,
    }
