"""
Pydantic models for notification API requests and responses.

`user_id` is a plain string reference to the user service.
`id` in responses is the hex string form of the notification document `_id`.
Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationType = Literal[
    "order_placed",
    "order_confirmed",
    "order_shipped",
    "order_delivered",
    "order_cancelled",
    "payment_confirmed",
    "payment_failed",
    "review_posted",
    "general",
]


class NotificationCreate(BaseModel):
    """Payload for creating a notification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: Annotated[str, Field(min_length=1, max_length=200)]
    notification_type: NotificationType = "general"
    title: Annotated[str, Field(min_length=1, max_length=500)]
    message: Annotated[str, Field(min_length=1, max_length=10_000)]


class NotificationUpdate(BaseModel):
    """Payload for updating a notification — only sent fields are applied (partial update)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=500)] = None
    message: Annotated[str | None, Field(default=None, min_length=1, max_length=10_000)] = None


class NotificationResponse(BaseModel):
    """Notification returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    updated_at: datetime
