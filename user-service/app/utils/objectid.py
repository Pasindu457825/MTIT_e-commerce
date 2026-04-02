"""Helpers for validating MongoDB ObjectId strings in path parameters."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def parse_object_id(user_id: str) -> ObjectId:
    """
    Convert a route `user_id` string to `bson.ObjectId`.

    Raises HTTP 400 when the value cannot be parsed as an ObjectId.
    """
    user_id = user_id.strip()
    try:
        return ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user id — must be a valid MongoDB ObjectId string.",
        ) from None
