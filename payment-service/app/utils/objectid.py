"""Helpers for validating MongoDB ObjectId strings in path parameters."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def parse_object_id(payment_id: str) -> ObjectId:
    """
    Convert a route `payment_id` string to `bson.ObjectId`.

    Raises HTTP 400 when the value is empty or cannot be parsed as an ObjectId.
    """
    payment_id = payment_id.strip()
    if not payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payment_id cannot be empty.",
        ) from None
    try:
        return ObjectId(payment_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment id — must be a valid MongoDB ObjectId string.",
        ) from None
