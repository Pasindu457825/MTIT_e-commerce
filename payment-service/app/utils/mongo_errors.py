"""Helpers for interpreting MongoDB driver errors."""

from pymongo.errors import DuplicateKeyError


def is_duplicate_key_on_field(exc: DuplicateKeyError, field_name: str) -> bool:
    """
    Return True if this duplicate-key error is for the given document field.

    Used to retry only on `transaction_reference` collisions, not other unique indexes.
    """
    details = getattr(exc, "details", None) or {}
    key_value = details.get("keyValue")
    if isinstance(key_value, dict) and field_name in key_value:
        return True
    errmsg = str(details.get("errmsg", "")) + str(exc)
    if field_name in errmsg:
        return True
    if field_name == "transaction_reference" and "idx_transaction_reference_unique" in errmsg:
        return True
    return False
