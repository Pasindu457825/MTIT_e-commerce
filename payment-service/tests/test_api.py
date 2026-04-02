from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routes.payments import get_payment_service


def _now() -> datetime:
    return datetime.now(UTC)


class DummyPaymentService:
    async def create_payment(self, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "order_id": body.order_id,
            "user_id": body.user_id,
            "amount": body.amount,
            "payment_method": body.payment_method,
            "payment_status": "pending",
            "transaction_reference": "txn_demo",
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def get_payment(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "order_id": "order-1",
            "user_id": "user-1",
            "amount": 10.0,
            "payment_method": "card",
            "payment_status": "pending",
            "transaction_reference": "txn_demo",
            "created_at": _now(),
            "updated_at": _now(),
        }


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200


def test_create_and_get_payment() -> None:
    app.dependency_overrides[get_payment_service] = lambda: DummyPaymentService()
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/payments",
                json={"order_id": "order-1", "user_id": "user-1", "amount": 10.0, "payment_method": "card"},
            )
            get_one = client.get("/api/v1/payments/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert get_one.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_payment_create() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/payments",
            json={"order_id": "order-1", "user_id": "user-1", "amount": -10, "payment_method": "bad"},
        )
    assert res.status_code == 422


def test_invalid_objectid_payment() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/payments/not-an-objectid")
    assert res.status_code == 400


def test_not_found_payment() -> None:
    class NotFoundPaymentService(DummyPaymentService):
        async def get_payment(self, _oid):
            raise HTTPException(status_code=404, detail="Payment not found.")

    app.dependency_overrides[get_payment_service] = lambda: NotFoundPaymentService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/payments/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()
