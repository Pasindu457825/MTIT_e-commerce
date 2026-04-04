"""
Notification domain logic — CRUD, listing, and mark-as-read.

Routes stay thin: validate input → call this service → return schemas.
"""

from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.security import AuthenticatedUser, assert_owns_user_id
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationResponse
from app.utils.serialization import notification_document_to_response, notification_documents_to_responses


class NotificationService:
    """CRUD and listing for the `notifications` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.notifications_collection]

    async def create_notification(self, data: NotificationCreate) -> NotificationResponse:
        """Insert a new notification document."""
        now = datetime.now(UTC)
        doc = {
            "user_id": data.user_id.strip(),
            "notification_type": data.notification_type,
            "title": data.title.strip(),
            "message": data.message.strip(),
            "is_read": False,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(doc)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create notification — database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notification was created but could not be loaded.",
            )
        return notification_document_to_response(created)

    def _build_list_filter(
        self,
        *,
        user_id: str | None,
        is_read: bool | None,
    ) -> dict:
        q: dict = {}
        if user_id is not None and user_id.strip() != "":
            q["user_id"] = user_id.strip()
        if is_read is not None:
            q["is_read"] = is_read
        return q

    async def list_notifications(
        self,
        *,
        limit: int = 100,
        user_id: str | None = None,
        is_read: bool | None = None,
    ) -> list[NotificationResponse]:
        """Return notifications (newest first), with optional `user_id` / `is_read` filters."""
        query = self._build_list_filter(user_id=user_id, is_read=is_read)
        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list notifications — database error.",
            ) from exc
        return notification_documents_to_responses(docs)

    async def get_notification(
        self,
        notification_id: ObjectId,
        *,
        current_user: AuthenticatedUser | None = None,
    ) -> NotificationResponse:
        """Fetch one notification by `_id` or 404. Enforces ownership for non-admin users."""
        try:
            doc = await self._col.find_one({"_id": notification_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load notification — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )
        if current_user is not None:
            assert_owns_user_id(current_user, str(doc.get("user_id", "")))
        return notification_document_to_response(doc)

    async def update_notification(
        self, notification_id: ObjectId, data: NotificationUpdate
    ) -> NotificationResponse:
        """Partially update title and/or message; bumps `updated_at`."""
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if not payload:
            return await self.get_notification(notification_id)

        payload["updated_at"] = datetime.now(UTC)

        try:
            result = await self._col.update_one({"_id": notification_id}, {"$set": payload})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update notification — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )

        updated = await self._col.find_one({"_id": notification_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notification was updated but could not be loaded.",
            )
        return notification_document_to_response(updated)

    async def mark_as_read(
        self,
        notification_id: ObjectId,
        *,
        current_user: AuthenticatedUser | None = None,
    ) -> NotificationResponse:
        """Mark a notification as read; 404 if not found. Enforces ownership for non-admin users."""
        existing = await self.get_notification(notification_id, current_user=current_user)
        if existing.is_read:
            return existing
        now = datetime.now(UTC)
        try:
            result = await self._col.update_one(
                {"_id": notification_id},
                {"$set": {"is_read": True, "updated_at": now}},
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not mark notification as read — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )

        updated = await self._col.find_one({"_id": notification_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notification was updated but could not be loaded.",
            )
        return notification_document_to_response(updated)

    async def mark_all_read_for_user(self, user_id: str) -> dict:
        """Mark all unread notifications for a user as read."""
        now = datetime.now(UTC)
        try:
            result = await self._col.update_many(
                {"user_id": user_id.strip(), "is_read": False},
                {"$set": {"is_read": True, "updated_at": now}},
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not mark notifications as read — database error.",
            ) from exc
        return {"modified_count": result.modified_count}

    async def delete_notification(
        self,
        notification_id: ObjectId,
        *,
        current_user: AuthenticatedUser | None = None,
    ) -> None:
        """Delete a notification by id; 404 if not found. Enforces ownership for non-admin users."""
        await self.get_notification(notification_id, current_user=current_user)
        try:
            result = await self._col.delete_one({"_id": notification_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete notification — database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )
