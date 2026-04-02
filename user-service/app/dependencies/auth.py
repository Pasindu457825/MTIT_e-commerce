"""Authentication dependencies shared by routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.routes.users import get_user_service
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.utils.objectid import parse_object_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    svc: UserService = Depends(get_user_service),
) -> UserResponse:
    """Resolve authenticated user from bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization scheme must be Bearer.",
        )

    try:
        payload = decode_access_token(credentials.credentials)
        subject = str(payload.get("sub") or "")
        oid = parse_object_id(subject)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from None

    try:
        return await svc.get_user(oid)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token user no longer exists.",
            ) from None
        raise
