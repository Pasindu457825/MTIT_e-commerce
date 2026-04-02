from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import require_admin
from app.main import app
from app.routes.products import get_product_service


def _now() -> datetime:
    return datetime.now(UTC)


class DummyProductService:
    async def create_product(self, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "name": body.name,
            "description": body.description,
            "price": body.price,
            "category": body.category,
            "stock": body.stock,
            "image_url": body.image_url,
            "created_at": _now(),
            "updated_at": _now(),
        }


def _admin_user() -> dict:
    return {"sub": "507f1f77bcf86cd799439099", "email": "admin@example.com", "role": "admin"}

    async def get_product(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "name": "Phone",
            "description": "Smartphone",
            "price": 999.0,
            "category": "electronics",
            "stock": 10,
            "image_url": "",
            "created_at": _now(),
            "updated_at": _now(),
        }


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200


def test_create_and_get_product() -> None:
    app.dependency_overrides[get_product_service] = lambda: DummyProductService()
    app.dependency_overrides[require_admin] = lambda: _admin_user()
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/products",
                json={
                    "name": "Phone",
                    "description": "Smartphone",
                    "price": 999.0,
                    "category": "electronics",
                    "stock": 10,
                    "image_url": "",
                },
            )
            get_one = client.get("/api/v1/products/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert get_one.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_product_create() -> None:
    app.dependency_overrides[require_admin] = lambda: _admin_user()
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/products",
            json={"name": "", "price": -1, "stock": -1},
        )
    assert res.status_code == 422
    app.dependency_overrides.clear()


def test_invalid_objectid_product() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/products/badid")
    assert res.status_code == 400


def test_not_found_product() -> None:
    class NotFoundProductService(DummyProductService):
        async def get_product(self, _oid):
            raise HTTPException(status_code=404, detail="Product not found.")

    app.dependency_overrides[get_product_service] = lambda: NotFoundProductService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/products/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_product_writes_require_admin() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/products",
            json={
                "name": "Phone",
                "description": "Smartphone",
                "price": 999.0,
                "category": "electronics",
                "stock": 10,
                "image_url": "",
            },
        )
    assert res.status_code == 401
