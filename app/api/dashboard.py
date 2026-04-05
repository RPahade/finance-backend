"""
Dashboard routes — summary analytics and trend data.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    allow_analyst_admin,
    allow_all_authenticated,
)
from app.models.user import User
from app.schemas.dashboard import DashboardFilters
from app.services.dashboard_service import DashboardService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=dict,
    summary="Financial summary",
    description="Get total income, expenses, net balance, and record count. Analyst or Admin only.",
)
@limiter.limit("20/minute")
def get_summary(
    request: Request,
    date_from: date | None = Query(None, description="Start date (inclusive)"),
    date_to: date | None = Query(None, description="End date (inclusive)"),
    current_user: User = Depends(allow_analyst_admin),
    db: Session = Depends(get_db),
):
    """Get high-level financial summary."""
    filters = DashboardFilters(date_from=date_from, date_to=date_to)
    service = DashboardService(db)
    summary = service.get_summary(filters)
    return {
        "success": True,
        "data": summary.model_dump(),
        "message": "Summary retrieved successfully",
    }


@router.get(
    "/category-breakdown",
    response_model=dict,
    summary="Category-wise breakdown",
    description="Get income/expense totals per category. Analyst or Admin only.",
)
@limiter.limit("20/minute")
def get_category_breakdown(
    request: Request,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(allow_analyst_admin),
    db: Session = Depends(get_db),
):
    """Get breakdown of totals by category and type."""
    filters = DashboardFilters(date_from=date_from, date_to=date_to)
    service = DashboardService(db)
    breakdown = service.get_category_breakdown(filters)
    return {
        "success": True,
        "data": [item.model_dump() for item in breakdown],
        "message": "Category breakdown retrieved successfully",
    }


@router.get(
    "/trends",
    response_model=dict,
    summary="Monthly trends",
    description="Get monthly income, expense, and net trends. Analyst or Admin only.",
)
@limiter.limit("20/minute")
def get_trends(
    request: Request,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(allow_analyst_admin),
    db: Session = Depends(get_db),
):
    """Get monthly trend data for income and expenses."""
    filters = DashboardFilters(date_from=date_from, date_to=date_to)
    service = DashboardService(db)
    trends = service.get_monthly_trends(filters)
    return {
        "success": True,
        "data": [item.model_dump() for item in trends],
        "message": "Monthly trends retrieved successfully",
    }


@router.get(
    "/recent-activity",
    response_model=dict,
    summary="Recent activity",
    description="Get the most recent financial records. Available to all authenticated users.",
)
@limiter.limit("20/minute")
def get_recent_activity(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of recent records"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(allow_all_authenticated),
    db: Session = Depends(get_db),
):
    """Get recent financial activity for dashboard display."""
    filters = DashboardFilters(date_from=date_from, date_to=date_to)
    service = DashboardService(db)
    records = service.get_recent_activity(filters, limit=limit)
    return {
        "success": True,
        "data": [item.model_dump() for item in records],
        "message": "Recent activity retrieved successfully",
    }
