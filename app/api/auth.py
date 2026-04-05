"""
Authentication routes — register and login.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=201,
    summary="Register a new user",
    description="Create a new user account. Default role is 'viewer'.",
)
@limiter.limit("3/minute")
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with default Viewer role."""
    service = UserService(db)
    user = service.register(data)
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "message": "User registered successfully",
    }


@router.post(
    "/login",
    response_model=dict,
    summary="Login and get access token",
    description="Authenticate with email and password. Returns a JWT access token.",
)
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    service = UserService(db)
    token_data = service.authenticate(data)
    return {
        "success": True,
        "data": token_data,
        "message": "Login successful",
    }
