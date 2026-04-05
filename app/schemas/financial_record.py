"""
Pydantic schemas for financial records.
"""

from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.financial_record import RecordType


class FinancialRecordCreate(BaseModel):
    """Schema for creating a financial record."""
    amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2, description="Must be positive")
    type: RecordType
    category: str = Field(..., min_length=1, max_length=100)
    date: DateType
    description: Optional[str] = Field(None, max_length=1000)


class FinancialRecordUpdate(BaseModel):
    """Schema for updating a financial record (all fields optional)."""
    amount: Optional[Decimal] = Field(None, gt=0, max_digits=15, decimal_places=2)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[DateType] = None
    description: Optional[str] = Field(None, max_length=1000)


class FinancialRecordResponse(BaseModel):
    """Financial record returned in API responses."""
    id: int
    amount: Decimal
    type: RecordType
    category: str
    date: DateType
    description: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FinancialRecordFilters(BaseModel):
    """Query parameters for filtering financial records."""
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("date", pattern=r"^(date|amount|created_at|category)$")
    sort_order: str = Field("desc", pattern=r"^(asc|desc)$")
