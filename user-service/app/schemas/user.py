"""
Pydantic models for user API requests and responses.

Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalize_email(v: str) -> str:
    return v.strip().lower()


class UserRole(StrEnum):
    USER = "user"
    CUSTOMER = "customer"
    ADMIN = "admin"

class UserRoleInput(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """Payload for creating a user."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: Annotated[str, Field(min_length=1, max_length=200)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    role: UserRoleInput = UserRoleInput.USER
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
    password: Annotated[str | None, Field(default=None, min_length=8, max_length=128)] = None
    phone: Annotated[str | None, Field(default=None, max_length=40)] = None
    address: Annotated[str | None, Field(default=None, max_length=500)] = None
    role: UserRoleInput | None = None

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
    role: UserRole
    phone: str
    address: str
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Payload for authenticating an existing user."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_login(cls, v: str) -> str:
        if isinstance(v, str):
            return _normalize_email(v)
        return v


class AuthTokenResponse(BaseModel):
    """Bearer token response for authenticated clients."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
