"""
Seed script — populates the database with demo users and financial records.

Run with:  python seed.py
"""

import sys
import random
from datetime import date, timedelta
from decimal import Decimal

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, RecordType
from app.core.security import hash_password


# ----- Demo Data -----

USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "analyst@example.com",
        "username": "analyst",
        "password": "analyst123",
        "full_name": "Analyst User",
        "role": UserRole.ANALYST,
    },
    {
        "email": "viewer@example.com",
        "username": "viewer",
        "password": "viewer123",
        "full_name": "Viewer User",
        "role": UserRole.VIEWER,
    },
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Rental Income", "Dividends"]
EXPENSE_CATEGORIES = [
    "Food", "Rent", "Utilities", "Transport", "Entertainment",
    "Healthcare", "Education", "Shopping", "Insurance", "Other",
]


def seed_users(db) -> dict[str, User]:
    """Create demo users and return a mapping of username -> user."""
    users = {}
    for user_data in USERS:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"  User '{user_data['email']}' already exists, skipping.")
            users[user_data["username"]] = existing
            continue

        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        users[user_data["username"]] = user
        print(f"  Created user: {user_data['email']} (role: {user_data['role'].value})")

    return users


def seed_financial_records(db, admin_user: User, count: int = 50):
    """Generate sample financial records over the last 6 months."""
    existing_count = db.query(FinancialRecord).count()
    if existing_count > 0:
        print(f"  {existing_count} records already exist, skipping seed.")
        return

    today = date.today()
    records = []

    for i in range(count):
        # Random date within the last 6 months
        days_ago = random.randint(0, 180)
        record_date = today - timedelta(days=days_ago)

        # Roughly 40% income, 60% expense
        if random.random() < 0.4:
            record_type = RecordType.INCOME
            category = random.choice(INCOME_CATEGORIES)
            amount = Decimal(str(round(random.uniform(500, 15000), 2)))
        else:
            record_type = RecordType.EXPENSE
            category = random.choice(EXPENSE_CATEGORIES)
            amount = Decimal(str(round(random.uniform(50, 5000), 2)))

        record = FinancialRecord(
            amount=amount,
            type=record_type,
            category=category,
            date=record_date,
            description=f"Sample {record_type.value} entry for {category}",
            created_by=admin_user.id,
        )
        records.append(record)

    db.add_all(records)
    db.commit()
    print(f"  Created {count} sample financial records.")


def main():
    """Run the seed process."""
    print("\n=== Finance Backend — Database Seeder ===\n")

    # Ensure tables exist
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\nSeeding users...")
        users = seed_users(db)

        print("\nSeeding financial records...")
        seed_financial_records(db, admin_user=users["admin"], count=50)

        print("\n=== Seed Complete ===")
        print("\nDemo credentials:")
        print("  Admin:   admin@example.com   / admin123")
        print("  Analyst: analyst@example.com / analyst123")
        print("  Viewer:  viewer@example.com  / viewer123\n")

    except Exception as e:
        print(f"\nError during seeding: {e}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
