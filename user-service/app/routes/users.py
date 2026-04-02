"""
User REST endpoints under `/api/v1/users`.

Business rules and DB calls live in `app.services.user_service`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.user import UserCreate, UserUpdate, UserResponse
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
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by id",
)
async def get_user(
    user_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Fetch a single user by id."""
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
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Partially update a user (only provided fields are changed)."""
    oid = parse_object_id(user_id)
    return await svc.update_user(oid, body)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(
    user_id: Annotated[str, Path(description="MongoDB ObjectId as hex string")],
    svc: UserService = Depends(get_user_service),
) -> None:
    """Delete a user by id."""
    oid = parse_object_id(user_id)
    await svc.delete_user(oid)
