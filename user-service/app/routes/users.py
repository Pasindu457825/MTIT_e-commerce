"""
User REST endpoints under `/api/v1/users`.

Business rules and DB calls live in `app.services.user_service`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user, require_admin
from app.core.database import get_database
from app.schemas.user import UserCreate, UserRole, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.utils.objectid import parse_object_id

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    """Inject a `UserService` bound to the request’s MongoDB database."""
    return UserService(db)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    body: UserCreate,
    _admin: UserResponse = Depends(require_admin),
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a user; rejects duplicate emails with HTTP 409."""
    return await svc.create_user(body)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List users",
)
async def list_users(
    _admin: UserResponse = Depends(require_admin),
    svc: UserService = Depends(get_user_service),
    limit: Annotated[int, Query(ge=1, le=500, description="Max users to return")] = 100,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Search by full name, email, phone, or address",
        ),
    ] = None,
) -> list[UserResponse]:
    """Return users (newest first)."""
    return await svc.list_users(limit=limit, search=search)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get my profile",
)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Return currently authenticated user profile."""
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by id",
)
async def get_user(
    user_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    current_user: UserResponse = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Fetch a single user by id (admin or owner)."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own user profile.",
        )
    oid = parse_object_id(user_id)
    return await svc.get_user(oid)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    body: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Partially update a user (admin or owner)."""
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own user profile.",
        )
    if not is_admin and body.role is not None:
        # UX-friendly behavior: ignore role input for non-admin users
        # (Swagger often sends fields users didn't intend to change).
        body = body.model_copy(update={"role": None})
    oid = parse_object_id(user_id)
    return await svc.update_user(oid, body)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(
    user_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    _admin: UserResponse = Depends(require_admin),
    svc: UserService = Depends(get_user_service),
) -> None:
    """Delete a user by id."""
    oid = parse_object_id(user_id)
    await svc.delete_user(oid)
