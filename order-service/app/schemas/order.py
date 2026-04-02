"""
Pydantic models for order API requests and responses.

`user_id` and line `product_id` values are plain string references to other services.
`id` in responses is the hex string form of the MongoDB order document `_id`.
Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(StrEnum):
    """Allowed lifecycle values stored on each order."""

    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderLineItem(BaseModel):
    """One line on an order as returned to clients and stored in MongoDB."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: Annotated[str, Field(min_length=1, max_length=200)]
    quantity: Annotated[int, Field(gt=0)]
    unit_price: Annotated[float, Field(ge=0)]
    subtotal: Annotated[float, Field(ge=0)]

    @field_validator("unit_price", "subtotal", mode="after")
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("must be a finite number")
        return v


class OrderCreate(BaseModel):
    """Payload for creating an order — new orders are always created in `pending` status."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: Annotated[str, Field(min_length=1, max_length=200)]
    items: Annotated[list[OrderLineItem], Field(min_length=1)]
    total_amount: Annotated[float, Field(ge=0)]
    shipping_address: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("total_amount", mode="after")
    @classmethod
    def total_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("total_amount must be a finite number")
        return v


class OrderStatusUpdate(BaseModel):
    """Body for `PUT .../status` — only the target status is supplied."""

    status: OrderStatus


class OrderResponse(BaseModel):
    """Order returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    items: list[OrderLineItem]
    total_amount: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    updated_at: datetime
