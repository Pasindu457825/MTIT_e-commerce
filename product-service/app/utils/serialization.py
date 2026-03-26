"""
Reusable serialization from MongoDB documents to API models.

Keeps ObjectId → str conversion and datetime handling in one place.
"""

from datetime import UTC, datetime

from bson import ObjectId

from app.schemas.product import ProductResponse


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _float_price(value: object) -> float:
    """Normalize numeric price from BSON (int/float/Decimal) to float for JSON."""
    return float(value)


def product_document_to_response(doc: dict) -> ProductResponse:
    """
    Map a `products` collection document to `ProductResponse`.

    Expects keys: _id, name, description, price, category, stock, image_url, created_at, updated_at.
    """
    oid = doc.get("_id")
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    return ProductResponse(
        id=id_str,
        name=str(doc["name"]),
        description=str(doc.get("description", "") or ""),
        price=_float_price(doc["price"]),
        category=str(doc.get("category", "") or ""),
        stock=int(doc.get("stock", 0)),
        image_url=str(doc.get("image_url", "") or ""),
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )


def product_documents_to_responses(docs: list[dict]) -> list[ProductResponse]:
    """Serialize a list of product documents."""
    return [product_document_to_response(d) for d in docs]
