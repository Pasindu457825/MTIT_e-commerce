"""
Cart line helpers: normalized product ids, duplicate-line merging, and total calculation.

Totals: sum of per-line `round(q * unit_price, 2)` then a final `round(..., 2)` on the sum
to limit float drift (same as typical POS-style line math).
"""

from __future__ import annotations


def normalize_product_id(value: object) -> str:
    """Canonical string for comparing/storing `product_id` references."""
    return str(value).strip()


def merge_duplicate_lines(items: list[dict]) -> list[dict]:
    """
    Collapse multiple rows with the same normalized `product_id`.

    Quantities add; `unit_price` follows the **last** row seen for that id (last price wins).
    Rows with empty/missing `product_id` are dropped.
    Preserves first-seen order of distinct product ids.
    """
    buckets: dict[str, dict] = {}
    order: list[str] = []
    for row in items:
        pid = normalize_product_id(row.get("product_id", ""))
        if not pid:
            continue
        q = int(row["quantity"])
        p = float(row["unit_price"])
        if pid not in buckets:
            buckets[pid] = {"product_id": pid, "quantity": q, "unit_price": p}
            order.append(pid)
        else:
            buckets[pid]["quantity"] = int(buckets[pid]["quantity"]) + q
            buckets[pid]["unit_price"] = p
    return [buckets[k] for k in order]


def compute_cart_total(items: list[dict]) -> float:
    """Sum of line subtotals; each line uses `round(q * p, 2)`."""
    total = 0.0
    for row in items:
        q = float(row["quantity"])
        p = float(row["unit_price"])
        total += round(q * p, 2)
    return round(total, 2)


def line_matches_product(row: dict, product_id: str) -> bool:
    """Whether this row is for the same product reference as `product_id` (path/body)."""
    return normalize_product_id(row.get("product_id", "")) == normalize_product_id(product_id)
