"""
Test fixtures for the finance backend test suite.

Uses a separate test database and provides pre-configured clients
with different role authentications.
"""

import pytest
from decimal import Decimal
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.database import Base
from app.core.dependencies import get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, RecordType
from app.config import get_settings

settings = get_settings()

# Use a separate test database — appends "_test" to the database name
TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/finance_db_test"

test_engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override the default DB dependency to use the test database."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def app():
    """Create a test FastAPI app instance with overridden DB dependency."""
    _app = create_app()
    _app.dependency_overrides[get_db] = override_get_db
    return _app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a clean DB session for each test, with rollback."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(app):
    """Provide a test HTTP client."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper fixtures — pre-created users and their auth tokens
# ---------------------------------------------------------------------------

@pytest.fixture()
def admin_user(db) -> User:
    """Get or create an admin user for testing."""
    user = db.query(User).filter(User.email == "testadmin@test.com").first()
    if not user:
        user = User(
            email="testadmin@test.com",
            username="testadmin",
            hashed_password=hash_password("password123"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture()
def analyst_user(db) -> User:
    """Get or create an analyst user for testing."""
    user = db.query(User).filter(User.email == "testanalyst@test.com").first()
    if not user:
        user = User(
            email="testanalyst@test.com",
            username="testanalyst",
            hashed_password=hash_password("password123"),
            full_name="Test Analyst",
            role=UserRole.ANALYST,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture()
def viewer_user(db) -> User:
    """Get or create a viewer user for testing."""
    user = db.query(User).filter(User.email == "testviewer@test.com").first()
    if not user:
        user = User(
            email="testviewer@test.com",
            username="testviewer",
            hashed_password=hash_password("password123"),
            full_name="Test Viewer",
            role=UserRole.VIEWER,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture()
def admin_token(admin_user) -> str:
    """JWT token for admin user."""
    return create_access_token({"sub": admin_user.id, "role": admin_user.role.value})


@pytest.fixture()
def analyst_token(analyst_user) -> str:
    """JWT token for analyst user."""
    return create_access_token({"sub": analyst_user.id, "role": analyst_user.role.value})


@pytest.fixture()
def viewer_token(viewer_user) -> str:
    """JWT token for viewer user."""
    return create_access_token({"sub": viewer_user.id, "role": viewer_user.role.value})


def auth_header(token: str) -> dict:
    """Helper to build Authorization header."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_record(db, admin_user) -> FinancialRecord:
    """Create a sample financial record for testing."""
    record = FinancialRecord(
        amount=Decimal("1500.00"),
        type=RecordType.INCOME,
        category="Salary",
        date=date.today(),
        description="Test salary record",
        created_by=admin_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
