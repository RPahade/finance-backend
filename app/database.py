"""
Database engine, session factory, and declarative Base.
Uses synchronous SQLAlchemy with pymysql driver for MySQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_size=10,
    max_overflow=20,
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
