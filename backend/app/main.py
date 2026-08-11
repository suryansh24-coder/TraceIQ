"""
TraceIQ - FastAPI Application Entry Point

Production-ready application bootstrap for the TraceIQ backend.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.investigate import router as investigate_router
from app.config import settings
from app.middleware.error_handler import global_exception_handler
from app.middleware.security import add_security_headers


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage TraceIQ application startup and shutdown lifecycle.
    """

    logger.info(
        "traceiq_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        demo_mode=settings.demo_mode,
    )

    try:
        yield

    finally:
        logger.info(
            "traceiq_shutting_down",
        )


app = FastAPI(
    title=settings.app_name,
    description=(
        "TraceIQ — AI-powered incident investigation and "
        "evidence-grounded root-cause analysis platform."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================================

app.add_exception_handler(
    Exception,
    global_exception_handler,
)


# ============================================================================
# SECURITY HEADERS
# ============================================================================


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    """
    Apply security headers to every HTTP response.
    """

    return await add_security_headers(
        request,
        call_next,
    )


# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(
    health_router,
    tags=["Health"],
)

app.include_router(
    investigate_router,
    prefix="/api/v1",
    tags=["Investigation"],
)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================


@app.get(
    "/",
    tags=["System"],
)
async def root():
    """
    Basic API information endpoint.
    """

    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode,
    }


# ============================================================================
# APPLICATION HEALTH
# ============================================================================


@app.get(
    "/api/v1/status",
    tags=["System"],
)
async def application_status():
    """
    Lightweight application status endpoint.
    """

    return {
        "service": settings.app_name,
        "status": "operational",
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode,
    }


__all__ = [
    "app",
]