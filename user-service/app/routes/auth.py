"""Authentication endpoints under `/api/v1/auth`."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.routes.users import get_user_service
from app.schemas.user import AuthTokenResponse, LoginRequest, UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: UserCreate,
    svc: UserService = Depends(get_user_service),
) -> AuthTokenResponse:
    user = await svc.create_user(body)
    return AuthTokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.auth_access_token_expire_minutes * 60,
        user=user,
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="Authenticate with email and password",
)
async def login(
    body: LoginRequest,
    svc: UserService = Depends(get_user_service),
) -> AuthTokenResponse:
    user = await svc.authenticate_user(str(body.email), body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return AuthTokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.auth_access_token_expire_minutes * 60,
        user=user,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
