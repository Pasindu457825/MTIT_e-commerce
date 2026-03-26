"""
Validate client-supplied line subtotals and order total against server-side math.

Raises `HTTPException` 400 with a clear message when totals do not match.
"""

from fastapi import HTTPException, status

from app.schemas.order import OrderCreate, OrderLineItem
from app.utils.order_items import expected_line_subtotal, expected_total_from_items


def _lines_to_dicts(lines: list[OrderLineItem]) -> list[dict]:
    return [
        {
            "product_id": line.product_id,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "subtotal": line.subtotal,
        }
        for line in lines
    ]


def validate_create_totals(body: OrderCreate) -> None:
    """
    Ensure each line's `subtotal` matches `round(q * unit_price, 2)` and that
    `total_amount` matches the rounded sum of those line subtotals.
    """
    for i, line in enumerate(body.items):
        expected = expected_line_subtotal(line.quantity, line.unit_price)
        got = round(float(line.subtotal), 2)
        if got != expected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Line {i}: subtotal {got} does not match quantity × unit_price "
                    f"(expected {expected})."
                ),
            )

    dict_rows = _lines_to_dicts(body.items)
    expected_total = expected_total_from_items(dict_rows)
    got_total = round(float(body.total_amount), 2)
    if got_total != expected_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"total_amount {got_total} does not match the sum of line subtotals "
                f"(expected {expected_total})."
            ),
        )
