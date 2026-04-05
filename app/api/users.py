"""
User management routes — CRUD operations with admin-only access.
"""

import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, allow_admin
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=dict,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's own profile."""
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user).model_dump(),
        "message": "Profile retrieved successfully",
    }


@router.get(
    "/",
    response_model=dict,
    summary="List all users (Admin only)",
    description="Returns a paginated list of all users. Requires Admin role.",
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """List all users with pagination (admin only)."""
    service = UserService(db)
    users, total = service.get_all_users(page=page, page_size=page_size)
    return {
        "success": True,
        "data": [UserResponse.model_validate(u).model_dump() for u in users],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": max(1, math.ceil(total / page_size)),
        },
    }


@router.get(
    "/{user_id}",
    response_model=dict,
    summary="Get user by ID (Admin only)",
    description="Returns a single user by their ID. Requires Admin role.",
)
def get_user(
    user_id: int,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Get a single user by ID (admin only)."""
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "message": "User retrieved successfully",
    }


@router.put(
    "/{user_id}",
    response_model=dict,
    summary="Update user (Admin only)",
    description="Update a user's profile, role, or active status. Requires Admin role.",
)
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Update user details (admin only)."""
    service = UserService(db)
    user = service.update_user(user_id, data, current_user)
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "message": "User updated successfully",
    }


@router.delete(
    "/{user_id}",
    response_model=dict,
    summary="Deactivate user (Admin only)",
    description="Soft-deactivate a user account. Requires Admin role.",
)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a user (admin only). Cannot deactivate self."""
    service = UserService(db)
    user = service.deactivate_user(user_id, current_user)
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "message": "User deactivated successfully",
    }
