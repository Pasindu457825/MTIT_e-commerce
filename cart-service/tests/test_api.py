from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routes.cart import get_cart_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DummyCartService:
    async def add_item(self, user_id, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": user_id,
            "items": [
                {"product_id": body.product_id, "quantity": body.quantity, "unit_price": body.unit_price}
            ],
            "total_amount": body.quantity * body.unit_price,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def get_cart(self, user_id):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": user_id,
            "items": [{"product_id": "prod-1", "quantity": 2, "unit_price": 10.0}],
            "total_amount": 20.0,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def remove_item(self, _uid, _pid):
        raise HTTPException(status_code=404, detail="Product is not in this cart.")


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200


def test_create_and_get_cart() -> None:
    app.dependency_overrides[get_cart_service] = lambda: DummyCartService()
    try:
        with TestClient(app) as client:
            add = client.post(
                "/api/v1/cart/user-1/items",
                json={"product_id": "prod-1", "quantity": 2, "unit_price": 10.0},
            )
            get_cart = client.get("/api/v1/cart/user-1")
        assert add.status_code == 200
        assert get_cart.status_code == 200
        assert get_cart.json()["user_id"] == "user-1"
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_cart_add() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/cart/user-1/items",
            json={"product_id": "prod-1", "quantity": 0, "unit_price": 10.0},
        )
    assert res.status_code == 422


def test_not_found_cart_item_remove() -> None:
    app.dependency_overrides[get_cart_service] = lambda: DummyCartService()
    try:
        with TestClient(app) as client:
            res = client.delete("/api/v1/cart/user-1/items/prod-x")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()

