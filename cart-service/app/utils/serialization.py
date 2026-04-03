"""
Reusable serialization from MongoDB cart documents to API models.

Cart documents use a Mongo `ObjectId` for `_id`, but `user_id` / `product_id` stay strings.

`total_amount` in the response is derived from merged line items so it always matches the listed rows.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.schemas.cart import CartLineItem, CartResponse
from app.utils.cart_items import compute_cart_total, merge_duplicate_lines, normalize_product_id


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive timezone.utc; make them explicitly timezone.utc-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _raw_items_to_rows(raw_items: object) -> list[dict]:
    """Turn BSON subdocuments into plain dicts for merge/total helpers; skip bad/empty rows."""
    if not isinstance(raw_items, list):
        return []
    rows: list[dict] = []
    for x in raw_items:
        if not isinstance(x, dict):
            continue
        pid = normalize_product_id(x.get("product_id", ""))
        if not pid:
            continue
        try:
            q = int(x["quantity"])
            p = float(x["unit_price"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append({"product_id": pid, "quantity": q, "unit_price": p})
    return rows


def cart_document_to_response(doc: dict) -> CartResponse:
    """
    Map a `carts` collection document to `CartResponse`.

    Expects: _id, user_id, items, created_at, updated_at.
    """
    oid = doc.get("_id")
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    merged = merge_duplicate_lines(_raw_items_to_rows(doc.get("items")))
    total = compute_cart_total(merged)
    items = [
        CartLineItem(
            product_id=r["product_id"],
            quantity=int(r["quantity"]),
            unit_price=float(r["unit_price"]),
        )
        for r in merged
    ]

    return CartResponse(
        id=id_str,
        user_id=str(doc["user_id"]),
        items=items,
        total_amount=total,
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )

