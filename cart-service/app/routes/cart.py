"""
Cart REST endpoints under `/api/v1/cart`.

`user_id` and `product_id` are string references (not Mongo ObjectIds).
Logic lives in `app.services.cart_service`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.cart import CartItemAdd, CartItemQuantityUpdate, CartResponse
from app.services.cart_service import CartService
from app.utils.path_params import require_reference_id

router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CartService:
    """Inject a `CartService` bound to the request’s MongoDB database."""
    return CartService(db)


@router.post(
    "/{user_id}/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add item to cart",
)
async def add_cart_item(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    body: CartItemAdd,
    svc: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Add a line or merge quantity if `product_id` already exists; recalculates total."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.add_item(uid, body)


@router.get(
    "/{user_id}",
    response_model=CartResponse,
    summary="Get cart",
)
async def get_cart(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    svc: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Return the cart for this user (creates an empty cart if none exists yet)."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.get_cart(uid)


@router.put(
    "/{user_id}/items/{product_id}",
    response_model=CartResponse,
    summary="Update line quantity",
)
async def update_cart_item_quantity(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    product_id: Annotated[str, Path(description="External product id (string reference)")],
    body: CartItemQuantityUpdate,
    svc: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Set quantity for an existing line (`quantity` must be > 0)."""
    uid = require_reference_id(user_id, field_name="user_id")
    pid = require_reference_id(product_id, field_name="product_id")
    return await svc.update_item_quantity(uid, pid, body)


@router.delete(
    "/{user_id}/items/{product_id}",
    response_model=CartResponse,
    summary="Remove line from cart",
)
async def remove_cart_item(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    product_id: Annotated[str, Path(description="External product id (string reference)")],
    svc: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Remove one product line; 404 if that product is not in the cart."""
    uid = require_reference_id(user_id, field_name="user_id")
    pid = require_reference_id(product_id, field_name="product_id")
    return await svc.remove_item(uid, pid)


@router.delete(
    "/{user_id}",
    response_model=CartResponse,
    summary="Clear cart",
)
async def clear_cart(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    svc: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Remove all items and set `total_amount` to 0 (cart row remains)."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.clear_cart(uid)
