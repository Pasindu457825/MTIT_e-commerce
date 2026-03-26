"""
Pydantic models for product API requests and responses.

Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    """Payload for creating a product."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=1, max_length=300)]
    description: Annotated[str, Field(default="", max_length=10_000)]
    price: Annotated[float, Field(ge=0)]
    category: Annotated[str, Field(default="", max_length=120)]
    stock: Annotated[int, Field(ge=0)]
    image_url: Annotated[str, Field(default="", max_length=2000)]

    @field_validator("price", mode="after")
    @classmethod
    def price_finite(cls, v: float) -> float:
        if v != v:  # NaN
            raise ValueError("price must be a finite number")
        return v


class ProductUpdate(BaseModel):
    """Payload for updating a product — only sent fields are applied (partial update)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[str | None, Field(default=None, min_length=1, max_length=300)] = None
    description: Annotated[str | None, Field(default=None, max_length=10_000)] = None
    price: Annotated[float | None, Field(default=None, ge=0)] = None
    category: Annotated[str | None, Field(default=None, max_length=120)] = None
    stock: Annotated[int | None, Field(default=None, ge=0)] = None
    image_url: Annotated[str | None, Field(default=None, max_length=2000)] = None

    @field_validator("price", mode="after")
    @classmethod
    def price_finite(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v != v:
            raise ValueError("price must be a finite number")
        return v


class ProductResponse(BaseModel):
    """Product returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    price: float
    category: str
    stock: int
    image_url: str
    created_at: datetime
    updated_at: datetime
