"""
Pydantic schemas for dashboard / analytics responses.
"""

from datetime import date as DateType
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.schemas.financial_record import FinancialRecordResponse


class DashboardSummary(BaseModel):
    """High-level financial summary."""
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    total_records: int


class CategoryBreakdown(BaseModel):
    """Income/expense total for a single category."""
    category: str
    type: str
    total: Decimal
    count: int


class MonthlyTrend(BaseModel):
    """Monthly aggregated income and expense."""
    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal


class DashboardFilters(BaseModel):
    """Optional date-range filter for dashboard endpoints."""
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
