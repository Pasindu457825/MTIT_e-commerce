"""
Product domain logic — database access, filters, and timestamps.

Routes stay thin: validate input → call this service → return schemas.
"""

from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.serialization import product_document_to_response, product_documents_to_responses


class ProductService:
    """CRUD and listing for the `products` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.products_collection]

    async def create_product(self, data: ProductCreate) -> ProductResponse:
        """Insert a new product."""
        now = datetime.now(UTC)
        doc = {
            "name": data.name,
            "description": data.description,
            "price": data.price,
            "category": data.category,
            "stock": data.stock,
            "image_url": data.image_url,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(doc)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create product — database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product was created but could not be loaded.",
            )
        return product_document_to_response(created)

    def _build_list_filter(
        self,
        *,
        category: str | None,
        min_price: float | None,
        max_price: float | None,
    ) -> dict:
        """Build MongoDB filter dict for list queries."""
        q: dict = {}
        if category is not None and category.strip() != "":
            q["category"] = category.strip()
        price_cond: dict = {}
        if min_price is not None:
            price_cond["$gte"] = min_price
        if max_price is not None:
            price_cond["$lte"] = max_price
        if price_cond:
            q["price"] = price_cond
        return q

    async def list_products(
        self,
        *,
        limit: int = 100,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[ProductResponse]:
        """
        Return products sorted by creation time (newest first).

        Optional filters: exact `category`, and/or `price` between `min_price` and `max_price`.
        """
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_price cannot be greater than max_price.",
            )

        query = self._build_list_filter(
            category=category,
            min_price=min_price,
            max_price=max_price,
        )
        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list products — database error.",
            ) from exc
        return product_documents_to_responses(docs)

    async def get_product(self, product_id: ObjectId) -> ProductResponse:
        """Fetch one product by `_id` or 404."""
        try:
            doc = await self._col.find_one({"_id": product_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load product — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )
        return product_document_to_response(doc)

    async def update_product(self, product_id: ObjectId, data: ProductUpdate) -> ProductResponse:
        """Apply partial updates; bumps `updated_at` to UTC now."""
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if not payload:
            # No fields to change — return current document
            return await self.get_product(product_id)

        payload["updated_at"] = datetime.now(UTC)

        try:
            result = await self._col.update_one({"_id": product_id}, {"$set": payload})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update product — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        updated = await self._col.find_one({"_id": product_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product was updated but could not be loaded.",
            )
        return product_document_to_response(updated)

    async def delete_product(self, product_id: ObjectId) -> None:
        """Delete a product by id; 404 if not found."""
        try:
            result = await self._col.delete_one({"_id": product_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete product — database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )
