"""
TraceIQ - Health API

Provides liveness and readiness endpoints for:
- Local development
- Docker
- Kubernetes
- Load balancers
- Monitoring systems

Endpoints:
    GET /health
        Lightweight liveness check.

    GET /health/ready
        Readiness check for application dependencies/configuration.

Health endpoints should remain lightweight and must never invoke the
LLM or run a full investigation.
"""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Response, status

from app.config import settings
from app.schemas.common import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
)


router = APIRouter(
    tags=["Health"],
)


# ============================================================================
# LIVENESS
# ============================================================================


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application liveness check",
    description=(
        "Returns whether the TraceIQ API process is alive. "
        "This endpoint intentionally performs no external dependency checks."
    ),
)
async def health_check() -> HealthResponse:
    """
    Lightweight liveness probe.

    This endpoint should remain extremely reliable. Kubernetes/Docker can use
    it to determine whether the application process itself is alive.
    """

    return HealthResponse(
        status=HealthStatus.HEALTHY,
        version=settings.version,
        environment=settings.app_env,
        components=[
            ComponentHealth(
                name="api",
                status=HealthStatus.HEALTHY,
                message="TraceIQ API process is running.",
            ),
        ],
    )


# ============================================================================
# READINESS
# ============================================================================


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Application readiness check",
    description=(
        "Checks whether TraceIQ is configured sufficiently to receive "
        "requests and reports the state of available integrations."
    ),
)
async def readiness_check(
    response: Response,
) -> HealthResponse:
    """
    Readiness probe.

    Unlike the liveness endpoint, this performs lightweight configuration
    checks.

    External services such as PostgreSQL and Qdrant will be checked here once
    their application-scoped clients are implemented. We deliberately do not
    make network calls from this endpoint yet because those clients are not
    part of the current dependency graph.
    """

    started = perf_counter()

    components: list[ComponentHealth] = []

    # ------------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------------

    components.append(
        ComponentHealth(
            name="api",
            status=HealthStatus.HEALTHY,
            message="API configuration loaded successfully.",
        )
    )

    # ------------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------------

    try:
        settings.validate_production()

        components.append(
            ComponentHealth(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Application configuration is valid.",
            )
        )

    except ValueError as exc:
        components.append(
            ComponentHealth(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
            )
        )

    # ------------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------------

    if settings.llm_provider == "ollama":
        components.append(
            ComponentHealth(
                name="llm",
                status=HealthStatus.HEALTHY,
                message="Ollama provider selected.",
            )
        )

    elif settings.llm_configured:
        components.append(
            ComponentHealth(
                name="llm",
                status=HealthStatus.HEALTHY,
                message=(
                    f"{settings.llm_provider} provider is configured."
                ),
            )
        )

    else:
        components.append(
            ComponentHealth(
                name="llm",
                status=(
                    HealthStatus.DEGRADED
                    if settings.demo_mode
                    else HealthStatus.UNHEALTHY
                ),
                message=(
                    "LLM credentials are not configured; "
                    "demo mode can continue without live LLM access."
                    if settings.demo_mode
                    else "LLM credentials are not configured."
                ),
            )
        )

    # ------------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------------

    if settings.github_configured:
        components.append(
            ComponentHealth(
                name="github",
                status=HealthStatus.HEALTHY,
                message="GitHub credentials are configured.",
            )
        )

    else:
        components.append(
            ComponentHealth(
                name="github",
                status=(
                    HealthStatus.DEGRADED
                    if settings.demo_mode
                    else HealthStatus.UNHEALTHY
                ),
                message=(
                    "GitHub credentials are not configured; "
                    "demo mode can use local data."
                    if settings.demo_mode
                    else "GitHub credentials are not configured."
                ),
            )
        )

    # ------------------------------------------------------------------------
    # RAG / QDRANT
    # ------------------------------------------------------------------------

    if settings.rag_enabled and settings.qdrant_configured:
        components.append(
            ComponentHealth(
                name="rag",
                status=HealthStatus.HEALTHY,
                message=(
                    f"RAG is enabled using collection "
                    f"'{settings.qdrant_collection}'."
                ),
            )
        )

    elif settings.demo_mode:
        components.append(
            ComponentHealth(
                name="rag",
                status=HealthStatus.DEGRADED,
                message=(
                    "RAG is not fully configured; demo data may be used."
                ),
            )
        )

    else:
        components.append(
            ComponentHealth(
                name="rag",
                status=HealthStatus.UNHEALTHY,
                message="RAG is enabled but Qdrant is not configured.",
            )
        )

    # ------------------------------------------------------------------------
    # REDIS
    # ------------------------------------------------------------------------

    if settings.redis_enabled and settings.redis_url:
        components.append(
            ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis configuration is available.",
            )
        )

    else:
        components.append(
            ComponentHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Redis-backed functionality is disabled.",
            )
        )

    # ------------------------------------------------------------------------
    # VOICE
    # ------------------------------------------------------------------------

    if not settings.voice_enabled:
        components.append(
            ComponentHealth(
                name="voice",
                status=HealthStatus.DEGRADED,
                message="Voice functionality is disabled.",
            )
        )

    elif settings.voice_configured:
        components.append(
            ComponentHealth(
                name="voice",
                status=HealthStatus.HEALTHY,
                message="Rime voice integration is configured.",
            )
        )

    else:
        components.append(
            ComponentHealth(
                name="voice",
                status=HealthStatus.DEGRADED,
                message="Voice is enabled but Rime credentials are missing.",
            )
        )

    # ------------------------------------------------------------------------
    # OVERALL STATUS
    # ------------------------------------------------------------------------

    unhealthy = any(
        component.status == HealthStatus.UNHEALTHY
        for component in components
    )

    degraded = any(
        component.status == HealthStatus.DEGRADED
        for component in components
    )

    if unhealthy:
        overall_status = HealthStatus.UNHEALTHY
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    elif degraded:
        overall_status = HealthStatus.DEGRADED
        response.status_code = status.HTTP_200_OK

    else:
        overall_status = HealthStatus.HEALTHY
        response.status_code = status.HTTP_200_OK

    elapsed_ms = (perf_counter() - started) * 1000

    components.append(
        ComponentHealth(
            name="health_check",
            status=HealthStatus.HEALTHY,
            latency_ms=round(elapsed_ms, 2),
            message="Readiness evaluation completed.",
        )
    )

    return HealthResponse(
        status=overall_status,
        version=settings.version,
        environment=settings.app_env,
        components=components,
    )


__all__ = [
    "router",
    "health_check",
    "readiness_check",
]