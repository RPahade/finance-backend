"""
Dashboard service — aggregation queries for analytics endpoints.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, extract, case
from sqlalchemy.orm import Session

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.dashboard import (
    DashboardSummary,
    CategoryBreakdown,
    MonthlyTrend,
    DashboardFilters,
)
from app.schemas.financial_record import FinancialRecordResponse


class DashboardService:
    """Handles dashboard analytics and aggregation logic."""

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self, filters: DashboardFilters):
        """Return a base query with non-deleted records and optional date range."""
        query = self.db.query(FinancialRecord).filter(
            FinancialRecord.is_deleted == False
        )
        if filters.date_from:
            query = query.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(FinancialRecord.date <= filters.date_to)
        return query

    def get_summary(self, filters: DashboardFilters) -> DashboardSummary:
        """
        Calculate overall financial summary:
        total income, total expenses, net balance, and record count.
        """
        base = self.db.query(
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("total_expenses"),
            func.count(FinancialRecord.id).label("total_records"),
        ).filter(FinancialRecord.is_deleted == False)

        if filters.date_from:
            base = base.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            base = base.filter(FinancialRecord.date <= filters.date_to)

        result = base.one()
        total_income = result.total_income or Decimal("0")
        total_expenses = result.total_expenses or Decimal("0")

        return DashboardSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net_balance=total_income - total_expenses,
            total_records=result.total_records,
        )

    def get_category_breakdown(self, filters: DashboardFilters) -> list[CategoryBreakdown]:
        """
        Get income/expense totals grouped by category and type.
        """
        query = (
            self.db.query(
                FinancialRecord.category,
                FinancialRecord.type,
                func.sum(FinancialRecord.amount).label("total"),
                func.count(FinancialRecord.id).label("count"),
            )
            .filter(FinancialRecord.is_deleted == False)
            .group_by(FinancialRecord.category, FinancialRecord.type)
            .order_by(func.sum(FinancialRecord.amount).desc())
        )

        if filters.date_from:
            query = query.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(FinancialRecord.date <= filters.date_to)

        rows = query.all()
        return [
            CategoryBreakdown(
                category=row.category,
                type=row.type.value,
                total=row.total,
                count=row.count,
            )
            for row in rows
        ]

    def get_monthly_trends(self, filters: DashboardFilters) -> list[MonthlyTrend]:
        """
        Get monthly aggregated income and expenses for trend analysis.
        """
        query = (
            self.db.query(
                extract("year", FinancialRecord.date).label("year"),
                extract("month", FinancialRecord.date).label("month"),
                func.coalesce(
                    func.sum(
                        case(
                            (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("total_income"),
                func.coalesce(
                    func.sum(
                        case(
                            (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                            else_=Decimal("0"),
                        )
                    ),
                    Decimal("0"),
                ).label("total_expenses"),
            )
            .filter(FinancialRecord.is_deleted == False)
            .group_by(
                extract("year", FinancialRecord.date),
                extract("month", FinancialRecord.date),
            )
            .order_by(
                extract("year", FinancialRecord.date),
                extract("month", FinancialRecord.date),
            )
        )

        if filters.date_from:
            query = query.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(FinancialRecord.date <= filters.date_to)

        rows = query.all()
        return [
            MonthlyTrend(
                year=int(row.year),
                month=int(row.month),
                total_income=row.total_income,
                total_expenses=row.total_expenses,
                net=row.total_income - row.total_expenses,
            )
            for row in rows
        ]

    def get_recent_activity(
        self, filters: DashboardFilters, limit: int = 10
    ) -> list[FinancialRecordResponse]:
        """
        Get the most recent financial records for quick dashboard view.
        """
        query = self._base_query(filters).order_by(
            FinancialRecord.date.desc(), FinancialRecord.created_at.desc()
        )

        records = query.limit(limit).all()
        return [FinancialRecordResponse.model_validate(r) for r in records]
