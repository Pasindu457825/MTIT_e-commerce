"""
Reusable serialization from MongoDB documents to API models.

Keeps ObjectId → str conversion and datetime handling in one place.
"""

from datetime import UTC, datetime

from bson import ObjectId

from app.schemas.review import ReviewResponse


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def review_document_to_response(doc: dict) -> ReviewResponse:
    """
    Map a `reviews` collection document to `ReviewResponse`.

    Expects keys: _id, product_id, user_id, rating, comment, created_at, updated_at.
    """
    oid = doc.get("_id")
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    return ReviewResponse(
        id=id_str,
        product_id=str(doc["product_id"]),
        user_id=str(doc["user_id"]),
        rating=int(doc["rating"]),
        comment=str(doc.get("comment", "") or ""),
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )


def review_documents_to_responses(docs: list[dict]) -> list[ReviewResponse]:
    """Serialize a list of review documents."""
    return [review_document_to_response(d) for d in docs]
