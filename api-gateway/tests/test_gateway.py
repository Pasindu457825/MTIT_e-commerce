import httpx
from fastapi.testclient import TestClient

from app.main import app


class FakeHttpClient:
    def __init__(self):
        self.calls: list[tuple[str, str, bytes | None]] = []

    async def aclose(self):
        return None

    async def request(self, method: str, url: str, headers=None, content=None):
        self.calls.append((method, url, content))
        req = httpx.Request(method, url)
        return httpx.Response(200, request=req, json={"ok": True})

    async def get(self, url: str):
        if url.endswith("/openapi.json"):
            service_key = {
                "8001": "users",
                "8002": "products",
                "8003": "orders",
                "8004": "payments",
                "8005": "cart",
                "8006": "reviews",
                "8007": "notifications",
            }[url.split(":")[-1].split("/")[0]]
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                request=req,
                json={
                    "openapi": "3.1.0",
                    "info": {"title": f"{service_key}-service", "version": "1.0.0"},
                    "paths": {
                        f"/api/v1/{service_key}": {
                            "get": {
                                "tags": [service_key],
                                "summary": f"List {service_key}",
                                "responses": {"200": {"description": "OK"}},
                            }
                        }
                    },
                    "tags": [{"name": service_key}],
                },
            )
        req = httpx.Request("GET", url)
        return httpx.Response(200, request=req, json={"status": "ok"})


def test_gateway_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_gateway_forwards_one_route_per_service_prefix() -> None:
    fake = FakeHttpClient()
    with TestClient(app) as client:
        client.app.state.http_client = fake
        for key in [
            "users",
            "products",
            "orders",
            "payments",
            "cart",
            "reviews",
            "notifications",
        ]:
            res = client.get(f"/api/v1/{key}")
            assert res.status_code == 200

    called_urls = [u for _, u, _ in fake.calls]
    assert any(u.endswith("/api/v1/users") for u in called_urls)
    assert any(u.endswith("/api/v1/products") for u in called_urls)
    assert any(u.endswith("/api/v1/orders") for u in called_urls)
    assert any(u.endswith("/api/v1/payments") for u in called_urls)
    assert any(u.endswith("/api/v1/cart") for u in called_urls)
    assert any(u.endswith("/api/v1/reviews") for u in called_urls)
    assert any(u.endswith("/api/v1/notifications") for u in called_urls)


def test_gateway_query_and_body_forwarding() -> None:
    fake = FakeHttpClient()
    with TestClient(app) as client:
        client.app.state.http_client = fake
        res = client.post("/api/v1/users?limit=10", json={"name": "Alice"})
    assert res.status_code == 200
    method, url, body = fake.calls[0]
    assert method == "POST"
    assert "limit=10" in url
    assert body is not None and b"Alice" in body


def test_gateway_timeout_and_unknown_service_errors() -> None:
    class TimeoutClient(FakeHttpClient):
        async def request(self, method: str, url: str, headers=None, content=None):
            raise httpx.TimeoutException("timeout", request=httpx.Request(method, url))

    with TestClient(app) as client:
        client.app.state.http_client = TimeoutClient()
        timeout_res = client.get("/api/v1/users")
        unknown_res = client.get("/api/v1/unknown")

    assert timeout_res.status_code == 504
    assert unknown_res.status_code == 404


def test_gateway_openapi_includes_downstream_paths() -> None:
    fake = FakeHttpClient()
    with TestClient(app) as client:
        client.app.state.http_client = fake
        res = client.get("/openapi.json")

    assert res.status_code == 200
    payload = res.json()
    assert "/health" in payload["paths"]
    assert "/api/v1/users" in payload["paths"]
    assert "/api/v1/products" in payload["paths"]
    assert "/api/v1/orders" in payload["paths"]
    assert "/api/v1/payments" in payload["paths"]
    assert "/api/v1/cart" in payload["paths"]
    assert "/api/v1/reviews" in payload["paths"]
    assert "/api/v1/notifications" in payload["paths"]
