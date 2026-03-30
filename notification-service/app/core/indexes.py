"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_notification_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure indexes for the `notifications` collection.

    - Index on `user_id` for fast per-user lookups.
    - Index on `is_read` for filtering unread notifications.
    - Index on `created_at` for newest-first ordering.
    """
    col = db[settings.notifications_collection]
    await col.create_index([("user_id", 1)], name="idx_user_id")
    await col.create_index([("user_id", 1), ("is_read", 1)], name="idx_user_id_is_read")
    await col.create_index([("created_at", -1)], name="idx_created_at")
