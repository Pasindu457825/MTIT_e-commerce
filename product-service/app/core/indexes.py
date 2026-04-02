"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_product_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure indexes for the `products` collection.

    Supports filtering by category and price range on list endpoints.
    """
    col = db[settings.products_collection]
    await col.create_index([("category", 1)], name="idx_category")
    await col.create_index([("price", 1)], name="idx_price")
    await col.create_index([("created_at", -1)], name="idx_created_at")
