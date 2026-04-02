"""
Review domain logic — CRUD, listing, and timestamps.

Routes stay thin: validate input → call this service → return schemas.
"""

from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.config import settings
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.utils.serialization import review_document_to_response, review_documents_to_responses


class ReviewService:
    """CRUD and listing for the `reviews` collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[settings.reviews_collection]

    async def create_review(self, data: ReviewCreate) -> ReviewResponse:
        """Insert a new review; 409 if this user already reviewed this product."""
        now = datetime.now(UTC)
        doc = {
            "product_id": data.product_id.strip(),
            "user_id": data.user_id.strip(),
            "rating": int(data.rating),
            "comment": data.comment or "",
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = await self._col.insert_one(doc)
        except DuplicateKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A review for this product already exists for this user.",
            ) from exc
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not create review — database error.",
            ) from exc

        created = await self._col.find_one({"_id": result.inserted_id})
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Review was created but could not be loaded.",
            )
        return review_document_to_response(created)

    def _build_list_filter(
        self,
        *,
        product_id: str | None,
        user_id: str | None,
    ) -> dict:
        q: dict = {}
        if product_id is not None and product_id.strip() != "":
            q["product_id"] = product_id.strip()
        if user_id is not None and user_id.strip() != "":
            q["user_id"] = user_id.strip()
        return q

    async def list_reviews(
        self,
        *,
        limit: int = 100,
        product_id: str | None = None,
        user_id: str | None = None,
    ) -> list[ReviewResponse]:
        """Return reviews (newest first), with optional `product_id` / `user_id` filters."""
        query = self._build_list_filter(product_id=product_id, user_id=user_id)
        try:
            cursor = self._col.find(query).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not list reviews — database error.",
            ) from exc
        return review_documents_to_responses(docs)

    async def get_review(self, review_id: ObjectId) -> ReviewResponse:
        """Fetch one review by `_id` or 404."""
        try:
            doc = await self._col.find_one({"_id": review_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not load review — database error.",
            ) from exc
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found.",
            )
        return review_document_to_response(doc)

    async def update_review(self, review_id: ObjectId, data: ReviewUpdate) -> ReviewResponse:
        """Partially update rating and/or comment; bumps `updated_at`."""
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if not payload:
            return await self.get_review(review_id)

        payload["updated_at"] = datetime.now(UTC)

        try:
            result = await self._col.update_one({"_id": review_id}, {"$set": payload})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not update review — database error.",
            ) from exc

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found.",
            )

        updated = await self._col.find_one({"_id": review_id})
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Review was updated but could not be loaded.",
            )
        return review_document_to_response(updated)

    async def delete_review(self, review_id: ObjectId) -> None:
        """Delete a review by id; 404 if not found."""
        try:
            result = await self._col.delete_one({"_id": review_id})
        except PyMongoError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not delete review — database error.",
            ) from exc
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found.",
            )
