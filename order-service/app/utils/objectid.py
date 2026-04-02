"""Helpers for validating MongoDB ObjectId strings in path parameters."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def parse_object_id(order_id: str) -> ObjectId:
    """
    Convert a route `order_id` string to `bson.ObjectId`.

    Raises HTTP 400 when the value is empty or cannot be parsed as an ObjectId.
    """
    order_id = order_id.strip()
    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_id cannot be empty.",
        ) from None
    try:
        return ObjectId(order_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order id — must be a valid MongoDB ObjectId string.",
        ) from None
