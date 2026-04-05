"""
FastAPI dependencies for database sessions, authentication, and RBAC.
"""

from typing import Generator, Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User, UserRole


# ---------------------------------------------------------------------------
# HTTP Bearer scheme — extracts token from "Authorization: Bearer <token>"
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for the duration of a request.
    Automatically closed when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT from the Authorization header and return the
    corresponding User object.

    Raises:
        UnauthorizedException: If the token is invalid, expired, or the user
                               does not exist or is inactive.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedException(detail="Invalid or expired token")

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException(detail="User not found")

    if not user.is_active:
        raise ForbiddenException(detail="User account is deactivated")

    return user


# ---------------------------------------------------------------------------
# Role-based access control dependency
# ---------------------------------------------------------------------------

class RoleChecker:
    """
    Dependency that restricts access to users with specific roles.

    Usage:
        allow_admin = RoleChecker([UserRole.ADMIN])

        @router.post("/", dependencies=[Depends(allow_admin)])
        def create_something(...): ...
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                detail=f"Role '{current_user.role.value}' does not have permission for this action"
            )
        return current_user


# ---------------------------------------------------------------------------
# Pre-built role checkers for convenience
# ---------------------------------------------------------------------------

allow_admin = RoleChecker([UserRole.ADMIN])
allow_analyst_admin = RoleChecker([UserRole.ANALYST, UserRole.ADMIN])
allow_all_authenticated = RoleChecker([UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN])
