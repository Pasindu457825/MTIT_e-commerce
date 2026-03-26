"""
Reusable serialization from MongoDB payment documents to API models.

Keeps ObjectId to str conversion, enum parsing, and datetime handling in one place.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.schemas.payment import PaymentResponse
from app.utils.payment_enums import parse_stored_payment_method, parse_stored_payment_status


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _require(doc: dict, key: str) -> object:
    if key not in doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment document is missing required field {key!r}.",
        )
    return doc[key]


def payment_document_to_response(doc: dict) -> PaymentResponse:
    """
    Map a payments collection document to PaymentResponse.

    Expects keys: _id, order_id, user_id, amount, payment_method, payment_status,
    transaction_reference, created_at, updated_at.
    """
    oid = doc.get("_id")
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document is missing _id.",
        )
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    try:
        raw_amount = _require(doc, "amount")
        amount = float(raw_amount)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document has invalid amount.",
        ) from exc

    if not math.isfinite(amount) or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document has invalid amount.",
        )

    order_id = str(_require(doc, "order_id")).strip()
    user_id = str(_require(doc, "user_id")).strip()
    if not order_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document has empty order_id or user_id.",
        )

    txn_ref = str(_require(doc, "transaction_reference")).strip()
    if not txn_ref:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document has empty transaction_reference.",
        )

    ca_raw = _require(doc, "created_at")
    ua_raw = _require(doc, "updated_at")
    if not isinstance(ca_raw, datetime) or not isinstance(ua_raw, datetime):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment document has invalid timestamps.",
        )
    created_at = _ensure_utc_aware(ca_raw)
    updated_at = _ensure_utc_aware(ua_raw)

    return PaymentResponse(
        id=id_str,
        order_id=order_id,
        user_id=user_id,
        amount=round(amount, 2),
        payment_method=parse_stored_payment_method(_require(doc, "payment_method")),
        payment_status=parse_stored_payment_status(_require(doc, "payment_status")),
        transaction_reference=txn_ref,
        created_at=created_at,
        updated_at=updated_at,
    )


def payment_documents_to_responses(docs: list[dict]) -> list[PaymentResponse]:
    """Serialize a list of payment documents."""
    return [payment_document_to_response(d) for d in docs]
