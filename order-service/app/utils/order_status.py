"""
Order lifecycle: parse stored status values and validate transitions.

Stored `status` in MongoDB is a lowercase string; unknown values are treated as data errors.
"""

from fastapi import HTTPException, status

from app.schemas.order import OrderStatus

# Allowed transitions from each current status (linear flow + cancel from early states).
_NEXT: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.pending: frozenset({OrderStatus.confirmed, OrderStatus.cancelled}),
    OrderStatus.confirmed: frozenset({OrderStatus.shipped, OrderStatus.cancelled}),
    OrderStatus.shipped: frozenset({OrderStatus.delivered}),
    OrderStatus.delivered: frozenset(),
    OrderStatus.cancelled: frozenset(),
}


def parse_stored_order_status(raw: object) -> OrderStatus:
    """
    Parse a BSON/string status into `OrderStatus`.

    Raises HTTP 500 when the stored value is not a known status (corrupt or legacy data).
    """
    s = str(raw).strip().lower()
    try:
        return OrderStatus(s)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid stored order status: {raw!r}",
        ) from None


def assert_status_transition_allowed(*, current: OrderStatus, new: OrderStatus) -> None:
    """
    Ensure `new` is reachable from `current`.

    Caller must handle `new == current` (idempotent no-op) before calling this.
    """
    allowed = _NEXT.get(current, frozenset())
    if new not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition order status from '{current.value}' to '{new.value}'.",
        )
