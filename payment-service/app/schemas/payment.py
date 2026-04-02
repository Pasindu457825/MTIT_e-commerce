"""
Pydantic models for payment API requests and responses.

`order_id` and `user_id` are plain string references (e.g. order Mongo `_id` as hex).
`id` in responses is the hex string form of the payment document `_id`.
Timestamps in responses are timezone-aware UTC datetimes (ISO-8601 in JSON).
"""

import math
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentMethod(StrEnum):
    """Allowed payment rails."""

    card = "card"
    cash_on_delivery = "cash_on_delivery"
    bank_transfer = "bank_transfer"


class PaymentStatus(StrEnum):
    """Payment lifecycle values stored on each payment."""

    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class PaymentCreate(BaseModel):
    """Payload for creating a payment — status starts as `pending`; reference is server-generated."""

    model_config = ConfigDict(str_strip_whitespace=True)

    order_id: Annotated[str, Field(min_length=1, max_length=200)]
    user_id: Annotated[str, Field(min_length=1, max_length=200)]
    amount: Annotated[float, Field(gt=0)]
    payment_method: PaymentMethod

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method_input(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("amount", mode="after")
    @classmethod
    def amount_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("amount must be a finite number")
        return float(v)


class PaymentStatusUpdate(BaseModel):
    """Body for `PUT .../status` — target `payment_status` only."""

    model_config = ConfigDict(extra="forbid")

    payment_status: PaymentStatus

    @field_validator("payment_status", mode="before")
    @classmethod
    def normalize_payment_status_input(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class PaymentResponse(BaseModel):
    """Payment returned to clients — `id` is the hex string form of MongoDB `_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    user_id: str
    amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    transaction_reference: str
    created_at: datetime
    updated_at: datetime
