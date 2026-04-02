"""
User domain logic: database access and rules (duplicate email, timestamps).

Routes stay thin: validate input -> call this service -> return schemas.
"""

import re
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserResponse, UserRole, UserRoleInput, UserUpdate
from app.utils.serialization import user_document_to_response, user_documents_to_responses


class UserService:
    """CRUD operations for the `users` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.users_collection]

    @staticmethod
    def _db_role_from_input(role: UserRoleInput) -> str:
        if role == UserRoleInput.ADMIN:
            return UserRole.ADMIN.value
        return UserRole.USER.value

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Insert a new user; returns 409 if email already exists."""
        now = datetime.now(UTC)
        email_norm = str(data.email).lower()
        doc = {
            "full_name": data.full_name,
            "email": email_norm,
            "password_hash": hash_password(data.password),
            "role": self._db_role_from_input(data.role),
            "phone": data.phone,
            "address": data.address,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(doc)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from None
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create user - database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User was created but could not be loaded.",
            )
        return user_document_to_response(created)

    async def list_users(self, *, limit: int = 100, search: str | None = None) -> list[UserResponse]:
        """Return users sorted by newest first, optionally filtered by keyword."""
        query: dict = {}
        if search:
            keyword = re.escape(search.strip())
            if keyword:
                query = {
                    "$or": [
                        {"full_name": {"$regex": keyword, "$options": "i"}},
                        {"email": {"$regex": keyword, "$options": "i"}},
                        {"phone": {"$regex": keyword, "$options": "i"}},
                        {"address": {"$regex": keyword, "$options": "i"}},
                    ]
                }

        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list users - database error.",
            ) from exc
        return user_documents_to_responses(docs)

    async def get_user(self, user_id: ObjectId) -> UserResponse:
        """Fetch one user by `_id` or 404."""
        try:
            doc = await self._col.find_one({"_id": user_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load user - database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user_document_to_response(doc)

    async def authenticate_user(self, email: str, password: str) -> UserResponse | None:
        """Return user when email/password are valid; otherwise `None`."""
        try:
            doc = await self._col.find_one({"email": email.strip().lower()})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not authenticate user - database error.",
            ) from exc

        if not doc:
            return None

        password_hash = str(doc.get("password_hash", ""))
        if not password_hash or not verify_password(password, password_hash):
            return None

        return user_document_to_response(doc)

    async def update_user(self, user_id: ObjectId, data: UserUpdate) -> UserResponse:
        """Apply partial updates; bumps `updated_at` to UTC now."""
        payload = data.model_dump(exclude_unset=True, exclude_none=True)
        if "email" in payload and payload["email"] is not None:
            payload["email"] = str(payload["email"]).lower()
        if "password" in payload and payload["password"] is not None:
            payload["password_hash"] = hash_password(payload.pop("password"))
        if "role" in payload and payload["role"] is not None:
            payload["role"] = self._db_role_from_input(payload["role"])

        if not payload:
            return await self.get_user(user_id)

        payload["updated_at"] = datetime.now(UTC)

        try:
            result = await self._col.update_one({"_id": user_id}, {"$set": payload})
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from None
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update user - database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        updated = await self._col.find_one({"_id": user_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User was updated but could not be loaded.",
            )
        return user_document_to_response(updated)

    async def delete_user(self, user_id: ObjectId) -> None:
        """Delete a user by id; 404 if not found."""
        try:
            result = await self._col.delete_one({"_id": user_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete user - database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
