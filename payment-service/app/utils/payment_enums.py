"""
Parse stored enum strings and validate payment_status transitions.
"""

from fastapi import HTTPException, status

from app.schemas.payment import PaymentMethod, PaymentStatus

_NEXT: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    PaymentStatus.pending: frozenset({PaymentStatus.completed, PaymentStatus.failed}),
    PaymentStatus.completed: frozenset({PaymentStatus.refunded}),
    PaymentStatus.failed: frozenset(),
    PaymentStatus.refunded: frozenset(),
}


def parse_stored_payment_method(raw: object) -> PaymentMethod:
    """Map BSON/string to PaymentMethod; HTTP 500 if missing, empty, or unknown."""
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_method.",
        )
    s = str(raw).strip().lower()
    if not s:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_method.",
        )
    try:
        return PaymentMethod(s)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_method.",
        ) from None


def parse_stored_payment_status(raw: object) -> PaymentStatus:
    """Map BSON/string to PaymentStatus; HTTP 500 if missing, empty, or unknown."""
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_status.",
        )
    s = str(raw).strip().lower()
    if not s:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_status.",
        )
    try:
        return PaymentStatus(s)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid stored payment_status.",
        ) from None


def assert_payment_status_transition_allowed(
    *,
    current: PaymentStatus,
    new: PaymentStatus,
) -> None:
    """
    Ensure new is reachable from current.

    Caller must handle new == current (idempotent no-op) before calling this.
    """
    allowed = _NEXT.get(current, frozenset())
    if new not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition payment_status from '{current.value}' to '{new.value}'."
            ),
        )
