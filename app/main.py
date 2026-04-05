"""
FastAPI application factory.

This is the entry point — creates the app, registers middleware,
exception handlers, and includes all routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import limiter
from slowapi.middleware import SlowAPIMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Creates database tables on startup (if they don't exist).
    """
    # Startup: create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: clean up resources if needed
    engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A finance dashboard backend with role-based access control, "
            "financial records management, and analytics APIs. "
            "Built with FastAPI, SQLAlchemy, and MySQL."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ---- CORS Middleware ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Rate Limiting Middleware ----
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # ---- Exception Handlers ----
    register_exception_handlers(app)

    # ---- Routes ----
    app.include_router(api_router)

    # ---- Health Check ----
    @app.get("/health", tags=["Health"])
    def health_check():
        """Simple health check endpoint."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


# Create the app instance (used by uvicorn)
app = create_app()
