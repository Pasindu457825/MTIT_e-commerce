"""
Product REST endpoints under `/api/v1/products`.

Business rules and DB calls live in `app.services.product_service`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.utils.objectid import parse_object_id

router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ProductService:
    """Inject a `ProductService` bound to the request’s MongoDB database."""
    return ProductService(db)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
async def create_product(
    body: ProductCreate,
    svc: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Create a product."""
    return await svc.create_product(body)


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List products",
)
async def list_products(
    svc: ProductService = Depends(get_product_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max products to return")] = 100,
    category: str | None = Query(default=None, description="Filter by exact category string"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price (inclusive)"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price (inclusive)"),
) -> list[ProductResponse]:
    """Return products (newest first), with optional category and price range filters."""
    return await svc.list_products(
        limit=limit,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by id",
)
async def get_product(
    product_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Fetch a single product by id."""
    oid = parse_object_id(product_id)
    return await svc.get_product(oid)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
)
async def update_product(
    product_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: ProductUpdate,
    svc: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Partially update a product (only provided fields are changed)."""
    oid = parse_object_id(product_id)
    return await svc.update_product(oid, body)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
async def delete_product(
    product_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: ProductService = Depends(get_product_service),
) -> None:
    """Delete a product by id."""
    oid = parse_object_id(product_id)
    await svc.delete_product(oid)
