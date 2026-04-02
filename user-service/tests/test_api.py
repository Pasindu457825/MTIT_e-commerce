from datetime import UTC, datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.routes.users import get_user_service
from app.schemas.user import UserResponse


def _now() -> datetime:
    return datetime.now(UTC)


class DummyUserService:
    async def create_user(self, body):
        return UserResponse(
            id="507f1f77bcf86cd799439011",
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
            address=body.address,
            created_at=_now(),
            updated_at=_now(),
        )

    async def get_user(self, _oid):
        return UserResponse(
            id="507f1f77bcf86cd799439011",
            full_name="Alice",
            email="alice@example.com",
            phone="0771234567",
            address="Colombo",
            created_at=_now(),
            updated_at=_now(),
        )

    async def authenticate_user(self, email: str, password: str):
        if email == "alice@example.com" and password == "StrongPass123":
            return await self.get_user(None)
        return None

    async def list_users(self, *, limit: int = 100, search: str | None = None):
        if search and "bob" in search.lower():
            return [
                UserResponse(
                    id="507f1f77bcf86cd799439012",
                    full_name="Bob",
                    email="bob@example.com",
                    phone="0710000000",
                    address="Kandy",
                    created_at=_now(),
                    updated_at=_now(),
                )
            ]
        return [
            UserResponse(
                id="507f1f77bcf86cd799439011",
                full_name="Alice",
                email="alice@example.com",
                phone="0771234567",
                address="Colombo",
                created_at=_now(),
                updated_at=_now(),
            )
        ]


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_and_get_user() -> None:
    app.dependency_overrides[get_user_service] = lambda: DummyUserService()
    try:
        with TestClient(app) as client:
            create = client.post(
                "/api/v1/users",
                json={
                    "full_name": "Alice",
                    "email": "alice@example.com",
                    "password": "StrongPass123",
                    "phone": "0771234567",
                    "address": "Colombo",
                },
            )
            get_one = client.get("/api/v1/users/507f1f77bcf86cd799439011")
        assert create.status_code == 201
        assert create.json()["email"] == "alice@example.com"
        assert get_one.status_code == 200
        assert get_one.json()["id"] == "507f1f77bcf86cd799439011"
    finally:
        app.dependency_overrides.clear()


def test_invalid_input_user_create() -> None:
    with TestClient(app) as client:
        res = client.post(
            "/api/v1/users",
            json={
                "full_name": "A",
                "email": "not-an-email",
                "password": "short",
                "phone": "",
                "address": "",
            },
        )
    assert res.status_code == 422


def test_invalid_objectid_user() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/users/not-an-objectid")
    assert res.status_code == 400


def test_not_found_user() -> None:
    class NotFoundUserService(DummyUserService):
        async def get_user(self, _oid):
            raise HTTPException(status_code=404, detail="User not found.")

    app.dependency_overrides[get_user_service] = lambda: NotFoundUserService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/users/507f1f77bcf86cd799439011")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_users_with_search() -> None:
    app.dependency_overrides[get_user_service] = lambda: DummyUserService()
    try:
        with TestClient(app) as client:
            res = client.get("/api/v1/users?search=bob&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["email"] == "bob@example.com"
    finally:
        app.dependency_overrides.clear()


def test_auth_register_login_and_me() -> None:
    app.dependency_overrides[get_user_service] = lambda: DummyUserService()
    try:
        with TestClient(app) as client:
            register = client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Alice",
                    "email": "alice@example.com",
                    "password": "StrongPass123",
                    "phone": "0771234567",
                    "address": "Colombo",
                },
            )
            assert register.status_code == 201
            token = register.json()["access_token"]
            me = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            login = client.post(
                "/api/v1/auth/login",
                json={"email": "alice@example.com", "password": "StrongPass123"},
            )
            bad_login = client.post(
                "/api/v1/auth/login",
                json={"email": "alice@example.com", "password": "WrongPass123"},
            )

        assert me.status_code == 200
        assert me.json()["email"] == "alice@example.com"
        assert login.status_code == 200
        assert "access_token" in login.json()
        assert bad_login.status_code == 401
    finally:
        app.dependency_overrides.clear()
