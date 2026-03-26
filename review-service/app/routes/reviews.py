"""
Review REST endpoints under `/api/v1/reviews`.

`review_id` paths use MongoDB ObjectId hex strings; `product_id` in nested routes is an
external product reference (plain string), consistent with cart-style references.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services.review_service import ReviewService
from app.utils.objectid import parse_object_id
from app.utils.path_params import require_reference_id

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Register `/product/{product_id}` before `/{review_id}` so the literal `product` segment
# is not parsed as a Mongo ObjectId.


def get_review_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ReviewService:
    """Inject a `ReviewService` bound to the request’s MongoDB database."""
    return ReviewService(db)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create review",
)
async def create_review(
    body: ReviewCreate,
    svc: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    """Create a review (one per user per product — unique index)."""
    return await svc.create_review(body)


@router.get(
    "",
    response_model=list[ReviewResponse],
    summary="List reviews",
)
async def list_reviews(
    svc: ReviewService = Depends(get_review_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max reviews to return")] = 100,
    product_id: str | None = Query(default=None, description="Filter by external product id"),
    user_id: str | None = Query(default=None, description="Filter by external user id"),
) -> list[ReviewResponse]:
    """Return reviews (newest first), optionally filtered by `product_id` and/or `user_id`."""
    return await svc.list_reviews(limit=limit, product_id=product_id, user_id=user_id)


@router.get(
    "/product/{product_id}",
    response_model=list[ReviewResponse],
    summary="List reviews for a product",
)
async def list_reviews_for_product(
    product_id: Annotated[str, Path(description="External product id (string reference)")],
    svc: ReviewService = Depends(get_review_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max reviews to return")] = 100,
) -> list[ReviewResponse]:
    """Return reviews for one product (newest first)."""
    pid = require_reference_id(product_id, field_name="product_id")
    return await svc.list_reviews(limit=limit, product_id=pid)


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Get review by id",
)
async def get_review(
    review_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    """Fetch a single review by id."""
    oid = parse_object_id(review_id)
    return await svc.get_review(oid)


@router.put(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Update review",
)
async def update_review(
    review_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: ReviewUpdate,
    svc: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    """Partially update a review (rating and/or comment)."""
    oid = parse_object_id(review_id)
    return await svc.update_review(oid, body)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review",
)
async def delete_review(
    review_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: ReviewService = Depends(get_review_service),
) -> None:
    """Delete a review by id."""
    oid = parse_object_id(review_id)
    await svc.delete_review(oid)
