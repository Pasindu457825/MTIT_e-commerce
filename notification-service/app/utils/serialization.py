"""
Reusable serialization from MongoDB documents to API models.

Keeps ObjectId → str conversion and datetime handling in one place.
"""

from datetime import UTC, datetime

from bson import ObjectId

from app.schemas.notification import NotificationResponse


def _ensure_utc_aware(dt: datetime) -> datetime:
    """BSON datetimes are often naive UTC; make them explicitly UTC-aware for JSON."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def notification_document_to_response(doc: dict) -> NotificationResponse:
    """
    Map a `notifications` collection document to `NotificationResponse`.

    Expects keys: _id, user_id, type, title, message, is_read, created_at, updated_at.
    """
    oid = doc.get("_id")
    if isinstance(oid, ObjectId):
        id_str = str(oid)
    else:
        id_str = str(oid)

    return NotificationResponse(
        id=id_str,
        user_id=str(doc["user_id"]),
        type=str(doc["type"]),
        title=str(doc["title"]),
        message=str(doc["message"]),
        is_read=bool(doc.get("is_read", False)),
        created_at=_ensure_utc_aware(doc["created_at"]),
        updated_at=_ensure_utc_aware(doc["updated_at"]),
    )


def notification_documents_to_responses(docs: list[dict]) -> list[NotificationResponse]:
    """Serialize a list of notification documents."""
    return [notification_document_to_response(d) for d in docs]
