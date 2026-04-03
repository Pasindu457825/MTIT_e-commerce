"""
Cart domain logic — one document per `user_id`, line items, and rolling `total_amount`.

Routes stay thin: validate path/body → call this service → return `CartResponse`.
"""

from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import settings
from app.schemas.cart import CartItemAdd, CartItemQuantityUpdate, CartResponse
from app.utils.cart_items import (
    compute_cart_total,
    line_matches_product,
    merge_duplicate_lines,
    normalize_product_id,
)
from app.utils.serialization import cart_document_to_response


class CartService:
    """Cart operations on the `carts` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.carts_collection]

    async def _persist_cart(self, cart_id: object, items: list[dict], *, now: datetime) -> CartResponse:
        """Normalize lines, recompute `total_amount`, persist, return API view."""
        items = merge_duplicate_lines(items)
        total = compute_cart_total(items)
        try:
            await self._col.update_one(
                {"_id": cart_id},
                {"$set": {"items": items, "total_amount": total, "updated_at": now}},
            )
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update cart — database error.",
            ) from exc
        doc = await self._col.find_one({"_id": cart_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cart was updated but could not be loaded.",
            )
        return cart_document_to_response(doc)

    async def get_or_create_cart(self, user_id: str) -> dict:
        """
        Return the cart document for `user_id`, inserting an empty cart if none exists.

        `user_id` must already be validated (non-empty string).
        """
        try:
            doc = await self._col.find_one({"user_id": user_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load cart — database error.",
            ) from exc

        if doc is not None:
            return doc

        now = datetime.now(timezone.utc)
        new_doc = {
            "user_id": user_id,
            "items": [],
            "total_amount": 0.0,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(new_doc)
        except DuplicateKeyError:
            doc = await self._col.find_one({"user_id": user_id})
            if doc is not None:
                return doc
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create cart — try again.",
            ) from None
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create cart — database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cart was created but could not be loaded.",
            )
        return created

    async def get_cart(self, user_id: str) -> CartResponse:
        """
        Return the cart for this user (creates an empty cart if needed).

        If legacy data had duplicate `product_id` rows, merge and persist once so Mongo
        matches the logical cart.
        """
        doc = await self.get_or_create_cart(user_id)
        raw = doc.get("items") or []
        cleaned = merge_duplicate_lines(deepcopy(raw))
        if len(cleaned) != len(raw):
            return await self._persist_cart(doc["_id"], cleaned, now=datetime.now(timezone.utc))
        return cart_document_to_response(doc)

    async def add_item(self, user_id: str, body: CartItemAdd) -> CartResponse:
        """
        Append a line; `_persist_cart` merges duplicate `product_id`s and recomputes total.

        If the same product already exists, merge combines quantities; `unit_price` follows
        the **last** appended row for that product (this request’s price).
        """
        cart = await self.get_or_create_cart(user_id)
        now = datetime.now(timezone.utc)
        items: list[dict] = deepcopy(cart.get("items") or [])

        pid = normalize_product_id(body.product_id)
        items.append(
            {
                "product_id": pid,
                "quantity": int(body.quantity),
                "unit_price": float(body.unit_price),
            }
        )

        return await self._persist_cart(cart["_id"], items, now=now)

    async def update_item_quantity(
        self,
        user_id: str,
        product_id: str,
        body: CartItemQuantityUpdate,
    ) -> CartResponse:
        """Set quantity for one product line; 404 if that product is not in the cart."""
        cart = await self.get_or_create_cart(user_id)
        now = datetime.now(timezone.utc)
        items: list[dict] = merge_duplicate_lines(deepcopy(cart.get("items") or []))

        updated = False
        for row in items:
            if line_matches_product(row, product_id):
                row["quantity"] = int(body.quantity)
                updated = True
                break

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product is not in this cart.",
            )

        return await self._persist_cart(cart["_id"], items, now=now)

    async def remove_item(self, user_id: str, product_id: str) -> CartResponse:
        """Remove one product line; 404 if that product is not present."""
        cart = await self.get_or_create_cart(user_id)
        now = datetime.now(timezone.utc)
        items: list[dict] = merge_duplicate_lines(deepcopy(cart.get("items") or []))

        new_items = [r for r in items if not line_matches_product(r, product_id)]
        if len(new_items) == len(items):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product is not in this cart.",
            )

        return await self._persist_cart(cart["_id"], new_items, now=now)

    async def clear_cart(self, user_id: str) -> CartResponse:
        """Remove all line items and reset `total_amount` to 0."""
        cart = await self.get_or_create_cart(user_id)
        now = datetime.now(timezone.utc)
        return await self._persist_cart(cart["_id"], [], now=now)

