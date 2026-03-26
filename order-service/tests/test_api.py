from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routes.orders import get_order_service


def _now() -> datetime:
    return datetime.now(UTC)


class DummyOrderService:
    async def create_order(self, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": body.user_id,
            "items": [x.model_dump() for x in body.items],
            "total_amount": body.total_amount,
            "status": "pending",
            "shipping_address": body.shipping_address,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def get_order(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": "user-1",
            "items": [{"product_id": "p1", "quantity": 1, "unit_price": 100.0, "subtotal": 100.0}],
            "total_amount": 100.0,
            "status": "pending",
            "shipping_address": "Colombo",
            "created_at": _now(),
            "updated_at": _now(),
        }


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200


def test_create_and_get_order() -> None:
    app.dependency_overrides[get_order_service] = lambda: DummyOrderService()
    try:
        payload = {
            "user_id": "user-1",
            "items": [{"product_id": "p1", "quantity": 1, "unit_price": 100.0, "subtotal": 100.0}],
            "total_amount": 100.0,
            "shipping_address": "Colombo",
        }
        with TestClient(app) as client:
            create = client.post("/api/v1/orders", json=payload)
            get_one = client.get("/api/v1/orders/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert get_one.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_order_create() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/orders",
            json={
                "user_id": "user-1",
                "items": [{"product_id": "p1", "quantity": 0, "unit_price": 100.0, "subtotal": 0.0}],
                "total_amount": 0.0,
                "shipping_address": "Colombo",
            },
        )
    assert res.status_code == 422


def test_invalid_objectid_order() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/orders/not-an-objectid")
    assert res.status_code == 400


def test_not_found_order() -> None:
    class NotFoundOrderService(DummyOrderService):
        async def get_order(self, _oid):
            raise HTTPException(status_code=404, detail="Order not found.")

    app.dependency_overrides[get_order_service] = lambda: NotFoundOrderService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/orders/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()
