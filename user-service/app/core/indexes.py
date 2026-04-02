"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_user_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure indexes for the `users` collection.

    Unique index on normalized email prevents duplicates at the database level (race-safe).
    """
    col = db[settings.users_collection]
    await col.create_index([("email", 1)], unique=True, name="uniq_email")
