"""
TraceIQ - Monitoring API Router

HTTP endpoints for retrieving normalized observability data.

Responsibilities:
- Validate API parameters.
- Call the monitoring integration.
- Return normalized monitoring data.
- Translate integration failures into HTTP responses.

This router does NOT:
- Perform root-cause analysis.
- Call an LLM.
- Build investigation evidence.
- Calculate confidence.
- Generate recommendations.

Those responsibilities belong to the service layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.integrations.monitoring import (
    MonitoringAPIError,
    MonitoringClient,
    MonitoringConfigurationError,
    MonitoringDataError,
    MonitoringIntegrationError,
    MonitoringTimeoutError,
)


router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)


# ============================================================================
# CLIENT
# ============================================================================


def _get_monitoring_client() -> MonitoringClient:
    """
    Create the monitoring client from application configuration.

    The client owns its HTTP connection pool and is closed after the request.
    This can later be replaced by an application-scoped client without
    changing the endpoint contract.
    """

    return MonitoringClient(
        settings=settings,
        base_url=settings.monitoring_api_url,
        api_key=(
            settings.monitoring_api_key.get_secret_value()
            if settings.monitoring_api_key
            else None
        ),
        provider_name=settings.monitoring_provider,
    )


# ============================================================================
# ERROR TRANSLATION
# ============================================================================


def _monitoring_http_exception(
    exc: MonitoringIntegrationError,
) -> HTTPException:
    """Translate monitoring integration errors into safe HTTP errors."""

    if isinstance(exc, MonitoringConfigurationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring integration is not configured.",
        )

    if isinstance(exc, MonitoringTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Monitoring provider request timed out.",
        )

    if isinstance(exc, MonitoringAPIError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Monitoring provider request failed.",
        )

    if isinstance(exc, MonitoringDataError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Monitoring provider returned invalid data.",
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Monitoring integration failed.",
    )


# ============================================================================
# METRICS
# ============================================================================


@router.get(
    "/metrics",
    summary="Get monitoring metrics",
    description="Retrieve normalized monitoring metrics for a service.",
)
async def get_metrics(
    service: str | None = Query(
        default=None,
        description="Service to investigate.",
    ),
    metric: list[str] | None = Query(
        default=None,
        description="Metric names to retrieve.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Start of the observation window.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of the observation window.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of metric observations.",
    ),
) -> list[dict[str, Any]]:
    """Retrieve normalized monitoring metrics."""

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time cannot be later than end_time.",
        )

    client = _get_monitoring_client()

    try:
        metrics = await client.query_metrics(
            service=service,
            metric_names=metric,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return [
            {
                "metric": item.metric,
                "value": item.value,
                "timestamp": item.timestamp,
                "unit": item.unit,
                "service": item.service,
                "environment": item.environment,
                "threshold": item.threshold,
                "source": item.source,
                "labels": dict(item.labels),
                "metadata": dict(item.metadata),
            }
            for item in metrics
        ]

    except MonitoringIntegrationError as exc:
        raise _monitoring_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# ALERTS
# ============================================================================


@router.get(
    "/alerts",
    summary="Get monitoring alerts",
    description="Retrieve normalized monitoring alerts.",
)
async def get_alerts(
    service: str | None = Query(
        default=None,
        description="Service associated with the alerts.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Start of the observation window.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of the observation window.",
    ),
    alert_status: str | None = Query(
        default=None,
        alias="status",
        description="Alert status filter.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> list[dict[str, Any]]:
    """Retrieve normalized monitoring alerts."""

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time cannot be later than end_time.",
        )

    client = _get_monitoring_client()

    try:
        alerts = await client.get_alerts(
            service=service,
            start_time=start_time,
            end_time=end_time,
            status=alert_status,
            limit=limit,
        )

        return [
            {
                "alert_id": item.alert_id,
                "name": item.name,
                "status": item.status,
                "severity": item.severity,
                "message": item.message,
                "timestamp": item.timestamp,
                "service": item.service,
                "environment": item.environment,
                "metric": item.metric,
                "value": item.value,
                "threshold": item.threshold,
                "source": item.source,
                "url": item.url,
                "labels": dict(item.labels),
                "metadata": dict(item.metadata),
            }
            for item in alerts
        ]

    except MonitoringIntegrationError as exc:
        raise _monitoring_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# ERRORS
# ============================================================================


@router.get(
    "/errors",
    summary="Get monitoring errors",
    description="Retrieve normalized application error events.",
)
async def get_errors(
    service: str | None = Query(
        default=None,
        description="Service associated with the errors.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Start of the observation window.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of the observation window.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> list[dict[str, Any]]:
    """Retrieve normalized monitoring error events."""

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time cannot be later than end_time.",
        )

    client = _get_monitoring_client()

    try:
        errors = await client.get_errors(
            service=service,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return [
            {
                "error_type": item.error_type,
                "message": item.message,
                "timestamp": item.timestamp,
                "service": item.service,
                "environment": item.environment,
                "count": item.count,
                "rate": item.rate,
                "source": item.source,
                "metadata": dict(item.metadata),
            }
            for item in errors
        ]

    except MonitoringIntegrationError as exc:
        raise _monitoring_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# SNAPSHOT
# ============================================================================


@router.get(
    "/snapshot",
    summary="Get monitoring snapshot",
    description=(
        "Collect metrics, alerts, and errors concurrently and return a "
        "bounded monitoring snapshot."
    ),
)
async def get_monitoring_snapshot(
    service: str | None = Query(
        default=None,
        description="Service to investigate.",
    ),
    environment: str | None = Query(
        default=None,
        description="Deployment environment.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Start of the observation window.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="End of the observation window.",
    ),
    metric: list[str] | None = Query(
        default=None,
        description="Metric names to include.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
) -> dict[str, Any]:
    """
    Collect a complete monitoring snapshot.

    The underlying integration fetches metrics, alerts, and errors
    concurrently.
    """

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time cannot be later than end_time.",
        )

    client = _get_monitoring_client()

    try:
        snapshot = await client.collect_snapshot(
            service=service,
            environment=environment,
            start_time=start_time,
            end_time=end_time,
            metric_names=metric,
            limit=limit,
        )

        return {
            "collected_at": snapshot.collected_at,
            "service": snapshot.service,
            "environment": snapshot.environment,
            "total_signals": snapshot.total_signals,
            "metrics": [
                {
                    "metric": item.metric,
                    "value": item.value,
                    "timestamp": item.timestamp,
                    "unit": item.unit,
                    "service": item.service,
                    "environment": item.environment,
                    "threshold": item.threshold,
                    "source": item.source,
                    "labels": dict(item.labels),
                    "metadata": dict(item.metadata),
                }
                for item in snapshot.metrics
            ],
            "alerts": [
                {
                    "alert_id": item.alert_id,
                    "name": item.name,
                    "status": item.status,
                    "severity": item.severity,
                    "message": item.message,
                    "timestamp": item.timestamp,
                    "service": item.service,
                    "environment": item.environment,
                    "metric": item.metric,
                    "value": item.value,
                    "threshold": item.threshold,
                    "source": item.source,
                    "url": item.url,
                    "labels": dict(item.labels),
                    "metadata": dict(item.metadata),
                }
                for item in snapshot.alerts
            ],
            "errors": [
                {
                    "error_type": item.error_type,
                    "message": item.message,
                    "timestamp": item.timestamp,
                    "service": item.service,
                    "environment": item.environment,
                    "count": item.count,
                    "rate": item.rate,
                    "source": item.source,
                    "metadata": dict(item.metadata),
                }
                for item in snapshot.errors
            ],
        }

    except MonitoringIntegrationError as exc:
        raise _monitoring_http_exception(exc) from exc

    finally:
        await client.aclose()


__all__ = [
    "router",
    "get_metrics",
    "get_alerts",
    "get_errors",
    "get_monitoring_snapshot",
]