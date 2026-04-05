"""
Common response wrapper schemas used across all endpoints.
Provides a consistent API response format.
"""

from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail in API responses."""
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response envelope."""
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Standard success response envelope (non-paginated)."""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Success"


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Standard paginated success response envelope."""
    success: bool = True
    data: list[Any] = []
    pagination: PaginationMeta
