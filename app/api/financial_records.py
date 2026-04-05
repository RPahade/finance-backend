"""
Financial records routes — CRUD with filtering, pagination, and RBAC.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
    allow_admin,
    allow_all_authenticated,
)
from app.models.user import User
from app.models.financial_record import RecordType
from app.schemas.financial_record import (
    FinancialRecordCreate,
    FinancialRecordUpdate,
    FinancialRecordFilters,
    FinancialRecordResponse,
)
from app.services.financial_service import FinancialService

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post(
    "/",
    response_model=dict,
    status_code=201,
    summary="Create a financial record (Admin only)",
    description="Create a new income or expense record. Requires Admin role.",
)
def create_record(
    data: FinancialRecordCreate,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Create a new financial record (admin only)."""
    service = FinancialService(db)
    record = service.create_record(data, user_id=current_user.id)
    return {
        "success": True,
        "data": FinancialRecordResponse.model_validate(record).model_dump(),
        "message": "Financial record created successfully",
    }


@router.get(
    "/",
    response_model=dict,
    summary="List financial records",
    description="Get paginated and filtered list of financial records. Available to all authenticated users.",
)
def list_records(
    type: RecordType | None = Query(None, description="Filter by income or expense"),
    category: str | None = Query(None, description="Filter by category name"),
    date_from: date | None = Query(None, description="Start date (inclusive)"),
    date_to: date | None = Query(None, description="End date (inclusive)"),
    min_amount: Decimal | None = Query(None, ge=0, description="Minimum amount"),
    max_amount: Decimal | None = Query(None, ge=0, description="Maximum amount"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("date", pattern=r"^(date|amount|created_at|category)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    current_user: User = Depends(allow_all_authenticated),
    db: Session = Depends(get_db),
):
    """List financial records with filtering and pagination."""
    filters = FinancialRecordFilters(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = FinancialService(db)
    records, total, total_pages = service.get_records(filters)
    return {
        "success": True,
        "data": [
            FinancialRecordResponse.model_validate(r).model_dump() for r in records
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    }


@router.get(
    "/{record_id}",
    response_model=dict,
    summary="Get a financial record by ID",
    description="Retrieve a single financial record. Available to all authenticated users.",
)
def get_record(
    record_id: int,
    current_user: User = Depends(allow_all_authenticated),
    db: Session = Depends(get_db),
):
    """Get a single financial record."""
    service = FinancialService(db)
    record = service.get_record_by_id(record_id)
    return {
        "success": True,
        "data": FinancialRecordResponse.model_validate(record).model_dump(),
        "message": "Record retrieved successfully",
    }


@router.put(
    "/{record_id}",
    response_model=dict,
    summary="Update a financial record (Admin only)",
    description="Update an existing financial record. Requires Admin role.",
)
def update_record(
    record_id: int,
    data: FinancialRecordUpdate,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Update a financial record (admin only)."""
    service = FinancialService(db)
    record = service.update_record(record_id, data)
    return {
        "success": True,
        "data": FinancialRecordResponse.model_validate(record).model_dump(),
        "message": "Record updated successfully",
    }


@router.delete(
    "/{record_id}",
    response_model=dict,
    summary="Delete a financial record (Admin only)",
    description="Soft-delete a financial record. Requires Admin role.",
)
def delete_record(
    record_id: int,
    current_user: User = Depends(allow_admin),
    db: Session = Depends(get_db),
):
    """Soft-delete a financial record (admin only)."""
    service = FinancialService(db)
    service.delete_record(record_id)
    return {
        "success": True,
        "data": None,
        "message": f"Record {record_id} deleted successfully",
    }
