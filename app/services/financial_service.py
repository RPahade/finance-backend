"""
Financial record service — CRUD operations with filtering and pagination.
"""

import math
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.financial_record import (
    FinancialRecordCreate,
    FinancialRecordUpdate,
    FinancialRecordFilters,
)
from app.core.exceptions import NotFoundException, BadRequestException


class FinancialService:
    """Handles financial record business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create_record(self, data: FinancialRecordCreate, user_id: int) -> FinancialRecord:
        """Create a new financial record."""
        record = FinancialRecord(
            amount=data.amount,
            type=data.type,
            category=data.category,
            date=data.date,
            description=data.description,
            created_by=user_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_record_by_id(self, record_id: int) -> FinancialRecord:
        """
        Get a single record by ID (excluding soft-deleted).

        Raises:
            NotFoundException: If the record does not exist or is soft-deleted.
        """
        record = (
            self.db.query(FinancialRecord)
            .filter(FinancialRecord.id == record_id, FinancialRecord.is_deleted == False)
            .first()
        )
        if not record:
            raise NotFoundException(
                detail=f"Financial record with ID {record_id} not found",
                error_code="RECORD_NOT_FOUND",
            )
        return record

    def get_records(self, filters: FinancialRecordFilters) -> tuple[list[FinancialRecord], int, int]:
        """
        Get paginated and filtered list of financial records.

        Returns:
            Tuple of (records list, total count, total pages).
        """
        query = self.db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)

        # Apply filters
        if filters.type:
            query = query.filter(FinancialRecord.type == filters.type)
        if filters.category:
            query = query.filter(FinancialRecord.category == filters.category)
        if filters.date_from:
            query = query.filter(FinancialRecord.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(FinancialRecord.date <= filters.date_to)
        if filters.min_amount is not None:
            query = query.filter(FinancialRecord.amount >= filters.min_amount)
        if filters.max_amount is not None:
            query = query.filter(FinancialRecord.amount <= filters.max_amount)

        # Total count before pagination
        total = query.count()
        total_pages = max(1, math.ceil(total / filters.page_size))

        # Sorting
        sort_column = getattr(FinancialRecord, filters.sort_by, FinancialRecord.date)
        sort_func = desc if filters.sort_order == "desc" else asc
        query = query.order_by(sort_func(sort_column))

        # Pagination
        records = (
            query
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .all()
        )

        return records, total, total_pages

    def update_record(self, record_id: int, data: FinancialRecordUpdate) -> FinancialRecord:
        """
        Update an existing financial record.

        Raises:
            NotFoundException: If the record does not exist.
            BadRequestException: If no fields are provided for update.
        """
        record = self.get_record_by_id(record_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise BadRequestException(
                detail="No fields provided for update",
                error_code="EMPTY_UPDATE",
            )

        for field, value in update_data.items():
            setattr(record, field, value)

        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_record(self, record_id: int) -> FinancialRecord:
        """
        Soft-delete a financial record by setting is_deleted = True.

        Raises:
            NotFoundException: If the record does not exist.
        """
        record = self.get_record_by_id(record_id)
        record.is_deleted = True
        self.db.commit()
        self.db.refresh(record)
        return record
