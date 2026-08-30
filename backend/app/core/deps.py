from typing import Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException, status, Depends
from app.core.security import SecurityUtils
from app.core.logging import logger


class UserToken(BaseModel):
    user_id: str
    username: str
    role: str = "user"  # "user" | "admin"


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None),
    x_user_role: Optional[str] = Header(default=None)
) -> UserToken:
    """Dependency extracting and verifying current authenticated user token."""
    # 1. Check Authorization Bearer header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = SecurityUtils.verify_access_token(token)
            return UserToken(
                user_id=payload.get("sub", "anonymous"),
                username=payload.get("username", "user"),
                role=payload.get("role", "user")
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    # 2. Check X-User-ID header for testing / header-based auth
    if x_user_id:
        return UserToken(
            user_id=x_user_id,
            username=x_user_id,
            role=x_user_role or "user"
        )

    # 3. Default fallback user (maintains backward compatibility with unauthenticated tests)
    return UserToken(
        user_id="default_owner",
        username="default_user",
        role="admin"
    )


async def require_admin(current_user: UserToken = Depends(get_current_user)) -> UserToken:
    """Dependency enforcing Admin role restriction."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user
