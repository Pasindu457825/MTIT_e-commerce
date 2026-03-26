"""
Reusable serialization from MongoDB order documents to API models.

ObjectId → str, UTC datetimes, and **recomputed** line subtotals / `total_amount` from
stored `quantity` and `unit_price` so responses always match line math (same as cart-style
totals even if `subtotal` / `total_amount` in Mongo were edited).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.schemas.order import OrderLineItem, OrderResponse
from app.utils.order_items import expected_line_subtotal, expected_total_from_items, normalize_product_id
from app.utils.order_status import parse_stored_order_status


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _normalized_lines_from_bson(raw_items: object) -> tuple[list[OrderLineItem], list[dict]]:
    """
    Build API line items and parallel dict rows for total math.

    Raises HTTP 500 on malformed lines (wrong types, missing fields, bad numbers).
    """
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order `items` must be an array.",
        )

    dict_rows: list[dict] = []
    for x in raw_items:
        if not isinstance(x, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Each order line must be an object.",
            )
        pid = normalize_product_id(x.get("product_id", ""))
        if not pid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order line has empty product_id.",
            )
        try:
            q = int(x["quantity"])
            p = float(x["unit_price"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order line has invalid quantity or unit_price.",
            ) from exc
        if q <= 0 or p < 0 or not math.isfinite(p):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Order line has invalid numeric fields.",
            )
        sub = expected_line_subtotal(q, p)
        dict_rows.append(
            {
                "product_id": pid,
                "quantity": q,
                "unit_price": p,
                "subtotal": sub,
            }
        )

    items = [
        OrderLineItem(
            product_id=r["product_id"],
            quantity=r["quantity"],
            unit_price=r["unit_price"],
            subtotal=r["subtotal"],
        )
        for r in dict_rows
    ]
    return items, dict_rows


def order_document_to_response(doc: dict) -> OrderResponse:
    """
    Map an `orders` collection document to `OrderResponse`.

    Expects keys: _id, user_id, items, total_amount, status, shipping_address, created_at, updated_at.
    """
    oid = doc.get("_id")
    if oid is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order document is missing _id.",
        )
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    items, dict_rows = _normalized_lines_from_bson(doc.get("items"))
    total_amount = expected_total_from_items(dict_rows)
    status_enum = parse_stored_order_status(doc["status"])

    return OrderResponse(
        id=id_str,
        user_id=str(doc["user_id"]),
        items=items,
        total_amount=total_amount,
        status=status_enum,
        shipping_address=str(doc["shipping_address"]),
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )


def order_documents_to_responses(docs: list[dict]) -> list[OrderResponse]:
    """Serialize a list of order documents."""
    return [order_document_to_response(d) for d in docs]
