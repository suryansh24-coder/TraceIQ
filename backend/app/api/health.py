from fastapi import APIRouter
from typing import Dict
from app.config import settings

router = APIRouter()

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok",
        "service": settings.app_name
    }

@router.get("/health/ready", response_model=Dict[str, str])
async def readiness_check():
    """
    Readiness check to verify application is fully ready to receive traffic.
    """
    # Here we could check DB connections, Qdrant availability, etc.
    # For MVP, it's just a basic check.
    return {
        "status": "ready",
        "service": settings.app_name,
        "mode": "demo" if settings.demo_mode else "production"
    }
