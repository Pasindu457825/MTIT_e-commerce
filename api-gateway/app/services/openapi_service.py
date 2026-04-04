"""Helpers for building one OpenAPI schema from the gateway and downstream services."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from httpx import AsyncClient, RequestError, TimeoutException

from app.core.config import settings


def _prefix_component_name(service_key: str, component_name: str) -> str:
    return f"{service_key}_{component_name}"


def _rewrite_refs(value: Any, ref_map: dict[str, str]) -> Any:
    """Recursively rewrite component references after renaming collisions."""
    if isinstance(value, dict):
        rewritten: dict[str, Any] = {}
        for key, inner in value.items():
            if key == "$ref" and isinstance(inner, str):
                rewritten[key] = ref_map.get(inner, inner)
            else:
                rewritten[key] = _rewrite_refs(inner, ref_map)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_refs(item, ref_map) for item in value]
    return value


def _merge_component_group(
    merged_group: dict[str, Any],
    incoming_group: dict[str, Any],
    group_name: str,
    service_key: str,
) -> None:
    ref_map: dict[str, str] = {}

    for component_name, component_schema in incoming_group.items():
        if component_name in merged_group and merged_group[component_name] != component_schema:
            target_name = _prefix_component_name(service_key, component_name)
            ref_map[f"#/components/{group_name}/{component_name}"] = (
                f"#/components/{group_name}/{target_name}"
            )

    for component_name, component_schema in incoming_group.items():
        target_name = ref_map.get(
            f"#/components/{group_name}/{component_name}",
            f"#/components/{group_name}/{component_name}",
        ).rsplit("/", 1)[-1]
        merged_group[target_name] = _rewrite_refs(deepcopy(component_schema), ref_map)


def _merge_components(
    merged_components: dict[str, Any],
    incoming_components: dict[str, Any],
    service_key: str,
) -> None:
    for group_name, group_payload in incoming_components.items():
        merged_group = merged_components.setdefault(group_name, {})
        _merge_component_group(
            merged_group,
            group_payload,
            group_name,
            service_key,
        )


def _merge_tags(merged_schema: dict[str, Any], incoming_tags: list[dict[str, Any]]) -> None:
    existing_names = {tag.get("name") for tag in merged_schema.setdefault("tags", [])}
    for tag in incoming_tags:
        if tag.get("name") not in existing_names:
            merged_schema["tags"].append(tag)
            existing_names.add(tag.get("name"))


def _base_gateway_schema(app: FastAPI) -> dict[str, Any]:
    """
    Build the gateway's own OpenAPI schema.

    The generic proxy routes stay hidden, but health and helper endpoints remain documented.
    """
    return get_openapi(
        title=settings.app_name,
        version="1.0.0",
        description="Gateway docs merged with downstream service APIs.",
        routes=app.routes,
    )


async def fetch_service_openapi(client: AsyncClient, service_key: str, base_url: str) -> dict[str, Any]:
    """Fetch one downstream service OpenAPI document."""
    url = f"{base_url.rstrip('/')}/openapi.json"
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except TimeoutException as exc:
        raise RuntimeError(
            f"Timed out while loading OpenAPI from '{service_key}' at {url}"
        ) from exc
    except RequestError as exc:
        raise RuntimeError(
            f"Could not reach '{service_key}' OpenAPI at {url}: {exc!s}"
        ) from exc


async def build_gateway_openapi(app: FastAPI) -> dict[str, Any]:
    """
    Merge the gateway schema with all downstream service schemas.

    Each downstream service already describes proxied paths like `/api/v1/users`,
    so the merged document can be served directly from the gateway.
    """
    client: AsyncClient = app.state.http_client
    merged_schema = _base_gateway_schema(app)
    merged_schema["servers"] = [{"url": "/"}]
    merged_schema.setdefault("components", {})

    unavailable_services: list[dict[str, str]] = []

    for service_key, base_url in settings.service_map.items():
        try:
            downstream_schema = await fetch_service_openapi(client, service_key, base_url)
        except RuntimeError as exc:
            unavailable_services.append({"service": service_key, "error": str(exc)})
            continue

        for path, methods in downstream_schema.get("paths", {}).items():
            merged_schema.setdefault("paths", {})[path] = methods
        _merge_components(
            merged_schema["components"],
            downstream_schema.get("components", {}),
            service_key,
        )
        _merge_tags(merged_schema, downstream_schema.get("tags", []))

    if unavailable_services:
        merged_schema["x-unavailable-services"] = unavailable_services

    return merged_schema
