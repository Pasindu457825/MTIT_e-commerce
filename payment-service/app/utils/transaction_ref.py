"""Generate unique `transaction_reference` values for new payments."""

from __future__ import annotations

import uuid


def new_transaction_reference() -> str:
    """
    Return a new unique reference (prefix + UUID hex).

    Uniqueness is also enforced by a unique MongoDB index on `transaction_reference`.
    """
    return f"txn_{uuid.uuid4().hex}"
