"""
Notification REST endpoints under `/api/v1/notifications`.

`notification_id` paths use MongoDB ObjectId hex strings; `user_id` in nested routes is an
external user reference (plain string), consistent with other service patterns.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationResponse
from app.services.notification_service import NotificationService
from app.utils.objectid import parse_object_id
from app.utils.path_params import require_reference_id

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Register `/user/{user_id}` before `/{notification_id}` so the literal `user` segment
# is not parsed as a Mongo ObjectId.


def get_notification_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> NotificationService:
    """Inject a `NotificationService` bound to the request's MongoDB database."""
    return NotificationService(db)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification",
)
async def create_notification(
    body: NotificationCreate,
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Create a new notification for a user."""
    return await svc.create_notification(body)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List notifications",
)
async def list_notifications(
    svc: NotificationService = Depends(get_notification_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max notifications to return")] = 100,
    user_id: str | None = Query(default=None, description="Filter by external user id"),
    is_read: bool | None = Query(default=None, description="Filter by read status"),
) -> list[NotificationResponse]:
    """Return notifications (newest first), optionally filtered by `user_id` and/or `is_read`."""
    return await svc.list_notifications(limit=limit, user_id=user_id, is_read=is_read)


@router.get(
    "/user/{user_id}",
    response_model=list[NotificationResponse],
    summary="List notifications for a user",
)
async def list_notifications_for_user(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    svc: NotificationService = Depends(get_notification_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max notifications to return")] = 100,
    is_read: bool | None = Query(default=None, description="Filter by read status"),
) -> list[NotificationResponse]:
    """Return notifications for one user (newest first), optionally filtered by `is_read`."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.list_notifications(limit=limit, user_id=uid, is_read=is_read)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get notification by id",
)
async def get_notification(
    notification_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Fetch a single notification by id."""
    oid = parse_object_id(notification_id)
    return await svc.get_notification(oid)


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Update notification",
)
async def update_notification(
    notification_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: NotificationUpdate,
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Partially update a notification (title and/or message)."""
    oid = parse_object_id(notification_id)
    return await svc.update_notification(oid, body)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
)
async def mark_notification_read(
    notification_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark a single notification as read."""
    oid = parse_object_id(notification_id)
    return await svc.mark_as_read(oid)


@router.patch(
    "/user/{user_id}/read-all",
    response_model=dict,
    summary="Mark all notifications as read for a user",
)
async def mark_all_notifications_read(
    user_id: Annotated[str, Path(description="External user id (string reference)")],
    svc: NotificationService = Depends(get_notification_service),
) -> dict:
    """Mark all unread notifications for a user as read."""
    uid = require_reference_id(user_id, field_name="user_id")
    return await svc.mark_all_read_for_user(uid)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
)
async def delete_notification(
    notification_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: NotificationService = Depends(get_notification_service),
) -> None:
    """Delete a notification by id."""
    oid = parse_object_id(notification_id)
    await svc.delete_notification(oid)
