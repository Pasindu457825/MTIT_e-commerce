"""
Validate string path parameters used as external references (e.g. `user_id`).

These are **not** Mongo ObjectIds — only non-empty trimmed strings.
"""

from fastapi import HTTPException, status


def require_reference_id(raw: str, *, field_name: str) -> str:
    """
    Return a stripped reference id or raise HTTP 400 if empty after trim.

    `field_name` is used in the error message (e.g. "user_id").
    """
    value = raw.strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty.",
        )
    return value
