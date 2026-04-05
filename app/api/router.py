"""
Aggregates all API sub-routers into a single router with /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.financial_records import router as records_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(records_router)
api_router.include_router(dashboard_router)
