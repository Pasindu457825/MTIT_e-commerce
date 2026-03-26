"""
Order domain logic — create, list, get, status transitions, delete.

Routes stay thin: validate path/body → call this service → return `OrderResponse`.
"""

from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.schemas.order import OrderCreate, OrderResponse, OrderStatus, OrderStatusUpdate
from app.utils.order_items import expected_total_from_items, items_for_storage
from app.utils.order_status import assert_status_transition_allowed, parse_stored_order_status
from app.utils.order_validation import validate_create_totals
from app.utils.serialization import order_document_to_response, order_documents_to_responses


class OrderService:
    """CRUD and listing for the `orders` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.orders_collection]

    async def create_order(self, body: OrderCreate) -> OrderResponse:
        """Create a new order in `pending` status with validated line math."""
        validate_create_totals(body)

        raw_lines = [li.model_dump() for li in body.items]
        stored_items = items_for_storage(raw_lines)
        if len(stored_items) != len(body.items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each line item must include a non-empty product_id.",
            )

        total = expected_total_from_items(stored_items)
        now = datetime.now(UTC)
        doc = {
            "user_id": body.user_id.strip(),
            "items": stored_items,
            "total_amount": total,
            "status": OrderStatus.pending.value,
            "shipping_address": body.shipping_address.strip(),
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(doc)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create order — database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order was created but could not be loaded.",
            )
        return order_document_to_response(created)

    def _build_list_filter(
        self,
        *,
        user_id: str | None,
        status: str | None,
    ) -> dict:
        q: dict = {}
        if user_id is not None and user_id.strip() != "":
            q["user_id"] = user_id.strip()
        if status is not None and status.strip() != "":
            q["status"] = status.strip().lower()
        return q

    async def list_orders(
        self,
        *,
        limit: int = 100,
        user_id: str | None = None,
        status: str | None = None,
    ) -> list[OrderResponse]:
        """Return orders (newest first), with optional `user_id` and/or `status` filters."""
        query = self._build_list_filter(user_id=user_id, status=status)
        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list orders — database error.",
            ) from exc
        return order_documents_to_responses(docs)

    async def get_order(self, order_id: ObjectId) -> OrderResponse:
        """Fetch one order by `_id` or 404."""
        try:
            doc = await self._col.find_one({"_id": order_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load order — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        return order_document_to_response(doc)

    async def update_order_status(
        self,
        order_id: ObjectId,
        body: OrderStatusUpdate,
    ) -> OrderResponse:
        """Apply a validated status transition; idempotent if status is unchanged."""
        try:
            doc = await self._col.find_one({"_id": order_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load order — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        current = parse_stored_order_status(doc["status"])
        new_status = body.status

        if new_status == current:
            return order_document_to_response(doc)

        assert_status_transition_allowed(current=current, new=new_status)

        now = datetime.now(UTC)
        try:
            result = await self._col.update_one(
                {"_id": order_id},
                {"$set": {"status": new_status.value, "updated_at": now}},
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update order status — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        updated = await self._col.find_one({"_id": order_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order was updated but could not be loaded.",
            )
        return order_document_to_response(updated)

    async def delete_order(self, order_id: ObjectId) -> None:
        """Delete an order by id; 404 if not found."""
        try:
            result = await self._col.delete_one({"_id": order_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete order — database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
