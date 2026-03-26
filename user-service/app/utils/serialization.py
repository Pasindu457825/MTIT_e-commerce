"""
Reusable serialization from MongoDB documents to API models.

Keeps ObjectId → str conversion and datetime handling in one place.
"""

from datetime import UTC, datetime

from bson import ObjectId

from app.schemas.user import UserResponse


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def user_document_to_response(doc: dict) -> UserResponse:
    """
    Map a `users` collection document to `UserResponse`.

    Expects keys: _id, full_name, email, phone, address, created_at, updated_at.
    """
    oid = doc.get("_id")
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    return UserResponse(
        id=id_str,
        full_name=str(doc["full_name"]),
        email=str(doc["email"]),
        phone=str(doc.get("phone", "") or ""),
        address=str(doc.get("address", "") or ""),
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )


def user_documents_to_responses(docs: list[dict]) -> list[UserResponse]:
    """Serialize a list of user documents."""
    return [user_document_to_response(d) for d in docs]
