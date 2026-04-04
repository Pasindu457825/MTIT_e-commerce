from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.routes.reviews import get_product_catalog_client, get_review_service


def _now() -> datetime:
    return datetime.now(UTC)


class DummyReviewService:
    async def create_review(self, body):
        return {
            "id": "507f1f77bcf86cd799439011",
            "product_id": body.product_id,
            "user_id": body.user_id,
            "rating": body.rating,
            "comment": body.comment,
            "created_at": _now(),
            "updated_at": _now(),
        }

    async def get_review(self, _oid):
        return {
            "id": "507f1f77bcf86cd799439011",
            "product_id": "prod-1",
            "user_id": "user-1",
            "rating": 5,
            "comment": "Great",
            "created_at": _now(),
            "updated_at": _now(),
        }


class DummyProductCatalogClient:
    async def assert_product_exists(self, _product_id: str) -> None:
        return None


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200


def test_create_and_get_review() -> None:
    app.dependency_overrides[get_review_service] = lambda: DummyReviewService()
    app.dependency_overrides[get_product_catalog_client] = lambda: DummyProductCatalogClient()
    old_flag = settings.validate_product_on_create
    settings.validate_product_on_create = True
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/reviews",
                json={"product_id": "prod-1", "user_id": "user-1", "rating": 5, "comment": "Great"},
            )
            get_one = client.get("/api/v1/reviews/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert get_one.status_code == 200
    finally:
        settings.validate_product_on_create = old_flag
        app.dependency_overrides.clear()


def test_invalid_input_review_create() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/reviews",
            json={"product_id": "prod-1", "user_id": "user-1", "rating": 10, "comment": "bad"},
        )
    assert res.status_code == 422


def test_invalid_objectid_review() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/reviews/not-an-objectid")
    assert res.status_code == 400


def test_not_found_review() -> None:
    class NotFoundReviewService(DummyReviewService):
        async def get_review(self, _oid):
            raise HTTPException(status_code=404, detail="Review not found.")

    app.dependency_overrides[get_review_service] = lambda: NotFoundReviewService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/reviews/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_create_review_returns_404_when_product_not_found() -> None:
    class ProductNotFoundClient:
        async def assert_product_exists(self, _product_id: str) -> None:
            raise HTTPException(status_code=404, detail="Product not found.")

    app.dependency_overrides[get_review_service] = lambda: DummyReviewService()
    app.dependency_overrides[get_product_catalog_client] = lambda: ProductNotFoundClient()
    old_flag = settings.validate_product_on_create
    settings.validate_product_on_create = True
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/reviews",
                json={
                    "product_id": "507f1f77bcf86cd799439012",
                    "user_id": "user-404",
                    "rating": 5,
                    "comment": "Great",
                },
            )
        assert create.status_code == 404
    finally:
        settings.validate_product_on_create = old_flag
        app.dependency_overrides.clear()
