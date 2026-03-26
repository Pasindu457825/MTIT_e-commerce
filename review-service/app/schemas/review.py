"""
Pydantic models for review API requests and responses.

`product_id` and `user_id` are plain string references to other services.
`id` in responses is the hex string form of the review document `_id`.
Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """Payload for creating a review."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: Annotated[str, Field(min_length=1, max_length=200)]
    user_id: Annotated[str, Field(min_length=1, max_length=200)]
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Annotated[str, Field(default="", max_length=10_000)]


class ReviewUpdate(BaseModel):
    """Payload for updating a review — only sent fields are applied (partial update)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    rating: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    comment: Annotated[str | None, Field(default=None, max_length=10_000)] = None


class ReviewResponse(BaseModel):
    """Review returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    user_id: str
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime
