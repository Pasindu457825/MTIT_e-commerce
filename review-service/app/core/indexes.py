"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_review_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure indexes for the `reviews` collection.

    Unique `(user_id, product_id)` enforces at most one review per user per product.
    """
    col = db[settings.reviews_collection]
    await col.create_index(
        [("user_id", 1), ("product_id", 1)],
        unique=True,
        name="idx_user_product_unique",
    )
    await col.create_index([("product_id", 1)], name="idx_product_id")
    await col.create_index([("created_at", -1)], name="idx_created_at")
