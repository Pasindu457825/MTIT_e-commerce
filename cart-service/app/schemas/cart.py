"""
Pydantic models for cart API requests and responses.

`user_id` and `product_id` are plain strings (references to other services), not Mongo ObjectIds.
Timestamps are timezone-aware UTC in responses (ISO-8601 in JSON).
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CartLineItem(BaseModel):
    """One row in a shopping cart."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: Annotated[str, Field(min_length=1, max_length=200)]
    quantity: Annotated[int, Field(gt=0)]
    unit_price: Annotated[float, Field(ge=0)]

    @field_validator("unit_price", mode="after")
    @classmethod
    def unit_price_finite(cls, v: float) -> float:
        if v != v:  # NaN
            raise ValueError("unit_price must be a finite number")
        return v


class CartItemAdd(BaseModel):
    """Body for adding a line to the cart (POST .../items)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: Annotated[str, Field(min_length=1, max_length=200)]
    quantity: Annotated[int, Field(gt=0)]
    unit_price: Annotated[float, Field(ge=0)]

    @field_validator("unit_price", mode="after")
    @classmethod
    def unit_price_finite(cls, v: float) -> float:
        if v != v:
            raise ValueError("unit_price must be a finite number")
        return v


class CartItemQuantityUpdate(BaseModel):
    """Body for updating quantity on an existing line (PUT .../items/{product_id})."""

    quantity: Annotated[int, Field(gt=0)]


class CartResponse(BaseModel):
    """Cart document returned to clients — `id` is the MongoDB `_id` of the cart row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    items: list[CartLineItem]
    total_amount: float
    created_at: datetime
    updated_at: datetime
