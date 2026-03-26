"""
Payment domain logic — create, list, get, status transitions, delete.

Routes stay thin: validate path/body -> call this service -> return PaymentResponse.
"""

from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import settings
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentStatus, PaymentStatusUpdate
from app.utils.payment_enums import (
    assert_payment_status_transition_allowed,
    parse_stored_payment_status,
)
from app.utils.mongo_errors import is_duplicate_key_on_field
from app.utils.serialization import payment_document_to_response, payment_documents_to_responses
from app.utils.transaction_ref import new_transaction_reference


class PaymentService:
    """CRUD and listing for the payments collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.payments_collection]

    async def create_payment(self, body: PaymentCreate) -> PaymentResponse:
        """Insert a new payment in pending status with a unique transaction_reference."""
        now = datetime.now(UTC)
        amount = round(float(body.amount), 2)
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="amount must be greater than 0.",
            )

        max_attempts = 5
        last_exc: Exception | None = None
        for _ in range(max_attempts):
            ref = new_transaction_reference()
            doc = {
                "order_id": body.order_id.strip(),
                "user_id": body.user_id.strip(),
                "amount": amount,
                "payment_method": body.payment_method.value,
                "payment_status": PaymentStatus.pending.value,
                "transaction_reference": ref,
                "created_at": now,
                "updated_at": now,
            }
            try:
                result = await self._col.insert_one(doc)
            except DuplicateKeyError as exc:
                if is_duplicate_key_on_field(exc, "transaction_reference"):
                    last_exc = exc
                    continue
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A payment with this data already exists (duplicate key).",
                ) from exc
            except PyMongoError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Could not create payment — database error.",
                ) from exc

            created = await self._col.find_one({"_id": result.inserted_id})
            if not created:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment was created but could not be loaded.",
                )
            return payment_document_to_response(created)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not allocate a unique transaction_reference — try again.",
        ) from last_exc

    def _build_list_filter(
        self,
        *,
        user_id: str | None,
        order_id: str | None,
        payment_status: str | None,
        payment_method: str | None,
    ) -> dict:
        q: dict = {}
        if user_id is not None and user_id.strip() != "":
            q["user_id"] = user_id.strip()
        if order_id is not None and order_id.strip() != "":
            q["order_id"] = order_id.strip()
        if payment_status is not None and payment_status.strip() != "":
            q["payment_status"] = payment_status.strip().lower()
        if payment_method is not None and payment_method.strip() != "":
            q["payment_method"] = payment_method.strip().lower()
        return q

    async def list_payments(
        self,
        *,
        limit: int = 100,
        user_id: str | None = None,
        order_id: str | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
    ) -> list[PaymentResponse]:
        """Return payments (newest first), with optional filters."""
        query = self._build_list_filter(
            user_id=user_id,
            order_id=order_id,
            payment_status=payment_status,
            payment_method=payment_method,
        )
        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list payments — database error.",
            ) from exc
        return payment_documents_to_responses(docs)

    async def get_payment(self, payment_id: ObjectId) -> PaymentResponse:
        """Fetch one payment by _id or 404."""
        try:
            doc = await self._col.find_one({"_id": payment_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load payment — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )
        return payment_document_to_response(doc)

    async def update_payment_status(
        self,
        payment_id: ObjectId,
        body: PaymentStatusUpdate,
    ) -> PaymentResponse:
        """Apply a validated payment_status transition; idempotent if unchanged."""
        try:
            doc = await self._col.find_one({"_id": payment_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load payment — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )

        current = parse_stored_payment_status(doc["payment_status"])
        new_status = body.payment_status

        if new_status == current:
            return payment_document_to_response(doc)

        assert_payment_status_transition_allowed(current=current, new=new_status)

        now = datetime.now(UTC)
        try:
            result = await self._col.update_one(
                {"_id": payment_id},
                {"$set": {"payment_status": new_status.value, "updated_at": now}},
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update payment status — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )

        updated = await self._col.find_one({"_id": payment_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment was updated but could not be loaded.",
            )
        return payment_document_to_response(updated)

    async def delete_payment(self, payment_id: ObjectId) -> None:
        """Delete a payment by id; 404 if not found."""
        try:
            result = await self._col.delete_one({"_id": payment_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete payment — database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )
