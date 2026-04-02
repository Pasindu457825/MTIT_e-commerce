"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_order_indexes(db: AsyncIOMotorDatabase) -> None:
    """Ensure indexes for the `orders` collection."""
    col = db[settings.orders_collection]
    await col.create_index([("user_id", 1)], name="idx_user_id")
    await col.create_index([("status", 1)], name="idx_status")
    await col.create_index([("created_at", -1)], name="idx_created_at")
