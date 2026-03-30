from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routes.notifications import get_notification_service


def _now() -> datetime:
    return datetime.now(UTC)


class DummyNotificationService:
    async def create_notification(self, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": body.user_id,
            "type": body.type,
            "title": body.title,
            "message": body.message,
            "is_read": False,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def get_notification(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": "user-1",
            "type": "order_placed",
            "title": "Order Placed",
            "message": "Your order has been placed successfully.",
            "is_read": False,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def mark_as_read(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "user_id": "user-1",
            "type": "order_placed",
            "title": "Order Placed",
            "message": "Your order has been placed successfully.",
            "is_read": True,
            "created_at": _now(),
            "updated_at": _now(),
        }


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["service"] == "notification-service"


def test_create_and_get_notification() -> None:
    app.dependency_overrides[get_notification_service] = lambda: DummyNotificationService()
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/notifications",
                json={
                    "user_id": "user-1",
                    "type": "order_placed",
                    "title": "Order Placed",
                    "message": "Your order has been placed successfully.",
                },
            )
            get_one = client.get("/api/v1/notifications/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert create.json()["user_id"] == "user-1"
        assert create.json()["is_read"] is False
        assert get_one.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_mark_notification_read() -> None:
    app.dependency_overrides[get_notification_service] = lambda: DummyNotificationService()
    try:
        with TestClient(app) as client:
            res = client.patch("/api/v1/notifications/507f1f77bcf86cd799439011/read")
        assert res.status_code == 200
        assert res.json()["is_read"] is True
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_notification_create() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/notifications",
            json={"user_id": "user-1", "type": "order_placed", "title": "", "message": "msg"},
        )
    assert res.status_code == 422


def test_invalid_objectid_notification() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/notifications/not-an-objectid")
    assert res.status_code == 400


def test_not_found_notification() -> None:
    class NotFoundService(DummyNotificationService):
        async def get_notification(self, _oid):
            raise HTTPException(status_code=404, detail="Notification not found.")

    app.dependency_overrides[get_notification_service] = lambda: NotFoundService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/notifications/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()
