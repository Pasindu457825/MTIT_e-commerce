"""
Line math for orders: per-line subtotals and order total (same rounding style as cart-service).

Each line subtotal is `round(quantity * unit_price, 2)`; the order total is the sum of those
line amounts, then `round(..., 2)`.
"""

from __future__ import annotations


def normalize_product_id(value: object) -> str:
    """Canonical string for storing and comparing `product_id` references."""
    return str(value).strip()


def expected_line_subtotal(quantity: int, unit_price: float) -> float:
    """Rounded line subtotal from quantity and unit price."""
    return round(float(quantity) * float(unit_price), 2)


def expected_total_from_items(items: list[dict]) -> float:
    """
    Sum of per-line expected subtotals from `quantity` and `unit_price` only.

    `items` are dicts with keys `quantity`, `unit_price`.
    """
    total = 0.0
    for row in items:
        q = int(row["quantity"])
        p = float(row["unit_price"])
        total += expected_line_subtotal(q, p)
    return round(total, 2)


def items_for_storage(items: list[dict]) -> list[dict]:
    """
    Normalize line dicts for MongoDB: strip product ids, int quantity, float prices,
    and set `subtotal` to the server-computed expected value.
    """
    out: list[dict] = []
    for row in items:
        pid = normalize_product_id(row.get("product_id", ""))
        if not pid:
            continue
        q = int(row["quantity"])
        p = float(row["unit_price"])
        sub = expected_line_subtotal(q, p)
        out.append(
            {
                "product_id": pid,
                "quantity": q,
                "unit_price": p,
                "subtotal": sub,
            }
        )
    return out
