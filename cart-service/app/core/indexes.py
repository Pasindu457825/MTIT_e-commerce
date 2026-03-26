"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_cart_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure indexes for the `carts` collection.

    One cart per logical `user_id` (string reference to the user-service identity).
    """
    col = db[settings.carts_collection]
    await col.create_index([("user_id", 1)], unique=True, name="uniq_user_id")
