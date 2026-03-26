"""
MongoDB index setup for this service.

Indexes are created idempotently on startup (`create_index` is safe to call repeatedly).
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings


async def ensure_payment_indexes(db: AsyncIOMotorDatabase) -> None:
    """Ensure indexes for the `payments` collection."""
    col = db[settings.payments_collection]
    await col.create_index(
        [("transaction_reference", 1)],
        unique=True,
        name="idx_transaction_reference_unique",
    )
    await col.create_index([("order_id", 1)], name="idx_order_id")
    await col.create_index([("user_id", 1)], name="idx_user_id")
    await col.create_index([("payment_status", 1)], name="idx_payment_status")
    await col.create_index([("payment_method", 1)], name="idx_payment_method")
    await col.create_index([("created_at", -1)], name="idx_created_at")
