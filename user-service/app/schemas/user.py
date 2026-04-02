"""
Pydantic models for user API requests and responses.

Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalize_email(v: str) -> str:
    return v.strip().lower()


class UserCreate(BaseModel):
    """Payload for creating a user."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Annotated[str, Field(min_length=1, max_length=200)]
    email: EmailStr
    phone: Annotated[str, Field(default="", max_length=40)]
    address: Annotated[str, Field(default="", max_length=500)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_create(cls, v: str) -> str:
        if isinstance(v, str):
            return _normalize_email(v)
        return v


class UserUpdate(BaseModel):
    """Payload for updating a user — only sent fields are applied (partial update)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Annotated[str | None, Field(default=None, min_length=1, max_length=200)] = None
    email: EmailStr | None = None
    phone: Annotated[str | None, Field(default=None, max_length=40)] = None
    address: Annotated[str | None, Field(default=None, max_length=500)] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_update(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return _normalize_email(v)
        return v


class UserResponse(BaseModel):
    """User returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    created_at: datetime
    updated_at: datetime
