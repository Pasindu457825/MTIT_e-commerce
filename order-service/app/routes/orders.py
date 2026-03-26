"""
Order REST endpoints under `/api/v1/orders`.

`order_id` paths use MongoDB ObjectId hex strings; `user_id` in `/user/{user_id}` is an
external user reference (plain string), consistent with other services.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.order import OrderCreate, OrderResponse, OrderStatus, OrderStatusUpdate
from app.services.order_service import OrderService
from app.utils.objectid import parse_object_id
from app.utils.path_params import require_reference_id

router = APIRouter(prefix="/orders", tags=["orders"])

# Register `/user/{user_id}` before `/{order_id}` so `user` is not treated as an order id.


def get_order_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> OrderService:
    """Inject an `OrderService` bound to the request’s MongoDB database."""
    return OrderService(db)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
)
async def create_order(
    body: OrderCreate,
    svc: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Create an order in `pending` status with validated line totals."""
    return await svc.create_order(body)


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List orders",
)
async def list_orders(
    svc: OrderService = Depends(get_order_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max orders to return")] = 100,
    user_id: str | None = Query(default=None, description="Filter by external user id"),
    order_status: OrderStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by order status",
    ),
) -> list[OrderResponse]:
    """Return orders (newest first), optionally filtered by `user_id` and/or `status`."""
    st = order_status.value if order_status is not None else None
    return await svc.list_orders(limit=limit, user_id=user_id, status=st)


@router.get(
    "/user/{user_id}",
    response_model=list[OrderResponse],
    summary="List orders for a user",
)
async def list_orders_for_user(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    svc: OrderService = Depends(get_order_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max orders to return")] = 100,
) -> list[OrderResponse]:
    """Return orders for one user (newest first)."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.list_orders(limit=limit, user_id=uid)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by id",
)
async def get_order(
    order_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Fetch a single order by id."""
    oid = parse_object_id(order_id)
    return await svc.get_order(oid)


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
async def update_order_status(
    order_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: OrderStatusUpdate,
    svc: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Apply a validated status transition."""
    oid = parse_object_id(order_id)
    return await svc.update_order_status(oid, body)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete order",
)
async def delete_order(
    order_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: OrderService = Depends(get_order_service),
) -> None:
    """Delete an order by id."""
    oid = parse_object_id(order_id)
    await svc.delete_order(oid)
