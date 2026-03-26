"""
Payment REST endpoints under `/api/v1/payments`.

`payment_id` paths use MongoDB ObjectId hex strings; `order_id` in `/order/{order_id}` is an
external order reference (plain string, e.g. order document id as hex).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.payment import (
    PaymentCreate,
    PaymentMethod,
    PaymentResponse,
    PaymentStatus,
    PaymentStatusUpdate,
)
from app.services.payment_service import PaymentService
from app.utils.objectid import parse_object_id
from app.utils.path_params import require_reference_id

router = APIRouter(prefix="/payments", tags=["payments"])

# Register `/order/{order_id}` before `/{payment_id}` so `order` is not parsed as an ObjectId.


def get_payment_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PaymentService:
    """Inject a PaymentService bound to the request's MongoDB database."""
    return PaymentService(db)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment",
)
async def create_payment(
    body: PaymentCreate,
    svc: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Create a payment in pending status with a server-generated transaction_reference."""
    return await svc.create_payment(body)


@router.get(
    "",
    response_model=list[PaymentResponse],
    summary="List payments",
)
async def list_payments(
    svc: PaymentService = Depends(get_payment_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max payments to return")] = 100,
    user_id: str | None = Query(default=None, description="Filter by external user id"),
    order_id: str | None = Query(default=None, description="Filter by external order id"),
    filter_payment_status: PaymentStatus | None = Query(
        default=None,
        alias="payment_status",
        description="Filter by payment_status",
    ),
    filter_payment_method: PaymentMethod | None = Query(
        default=None,
        alias="payment_method",
        description="Filter by payment_method",
    ),
) -> list[PaymentResponse]:
    """Return payments (newest first), optionally filtered."""
    st = filter_payment_status.value if filter_payment_status is not None else None
    mt = filter_payment_method.value if filter_payment_method is not None else None
    return await svc.list_payments(
        limit=limit,
        user_id=user_id,
        order_id=order_id,
        payment_status=st,
        payment_method=mt,
    )


@router.get(
    "/order/{order_id}",
    response_model=list[PaymentResponse],
    summary="List payments for an order",
)
async def list_payments_for_order(
    order_id: Annotated[str, Path(description="External order id (string reference)")],
    svc: PaymentService = Depends(get_payment_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max payments to return")] = 100,
) -> list[PaymentResponse]:
    """Return payments for one order (newest first)."""
    oid = require_reference_id(order_id, field_name="order_id")
    return await svc.list_payments(limit=limit, order_id=oid)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment by id",
)
async def get_payment(
    payment_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Fetch a single payment by id."""
    oid = parse_object_id(payment_id)
    return await svc.get_payment(oid)


@router.put(
    "/{payment_id}/status",
    response_model=PaymentResponse,
    summary="Update payment status",
)
async def update_payment_status(
    payment_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: PaymentStatusUpdate,
    svc: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Apply a validated payment_status transition."""
    oid = parse_object_id(payment_id)
    return await svc.update_payment_status(oid, body)


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete payment",
)
async def delete_payment(
    payment_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: PaymentService = Depends(get_payment_service),
) -> None:
    """Delete a payment by id."""
    oid = parse_object_id(payment_id)
    await svc.delete_payment(oid)
