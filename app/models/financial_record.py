"""
FinancialRecord ORM model for income/expense entries.
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Boolean, Enum, DateTime, Date,
    Numeric, Text, ForeignKey, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecordType(str, enum.Enum):
    """Type of financial record."""
    INCOME = "income"
    EXPENSE = "expense"


class FinancialRecord(Base):
    """A single financial transaction entry."""
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    type: Mapped[RecordType] = mapped_column(Enum(RecordType), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now()
    )

    # Relationship back to user
    creator = relationship("User", back_populates="financial_records")

    # Indexes for common query patterns
    __table_args__ = (
        Index("idx_records_type", "type"),
        Index("idx_records_category", "category"),
        Index("idx_records_date", "date"),
        Index("idx_records_created_by", "created_by"),
        Index("idx_records_type_date", "type", "date"),  # For dashboard aggregations
        Index("idx_records_soft_delete", "is_deleted"),
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialRecord(id={self.id}, type='{self.type.value}', "
            f"amount={self.amount}, category='{self.category}')>"
        )
