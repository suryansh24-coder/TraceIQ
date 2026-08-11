"""
TraceIQ - Monitoring Integration

Provider-agnostic monitoring adapter for TraceIQ.

This module provides a normalized interface for:
- Metrics
- Alerts
- Error-rate signals
- Latency signals
- Availability signals
- Generic observability events

The integration is deliberately provider-agnostic so TraceIQ can work with:
- A real monitoring provider
- A hackathon/demo monitoring API
- Static demo data
- A future Prometheus/Grafana integration
- Another observability platform

Responsibilities:
    External monitoring data
            ↓
    MonitoringClient
            ↓
    Normalized monitoring models
            ↓
    Evidence Builder

This module must NOT:
- Perform root-cause analysis.
- Call an LLM.
- Calculate investigation confidence.
- Generate recommendations.
- Contain API route logic.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import httpx

from app.config import Settings, get_settings


# ============================================================================
# EXCEPTIONS
# ============================================================================


class MonitoringIntegrationError(Exception):
    """Base exception for monitoring integration failures."""


class MonitoringConfigurationError(MonitoringIntegrationError):
    """Raised when monitoring integration is incorrectly configured."""


class MonitoringAPIError(MonitoringIntegrationError):
    """Raised when the monitoring provider returns an API error."""


class MonitoringTimeoutError(MonitoringIntegrationError):
    """Raised when a monitoring request times out."""


class MonitoringDataError(MonitoringIntegrationError):
    """Raised when monitoring data cannot be normalized safely."""


# ============================================================================
# NORMALIZED MODELS
# ============================================================================


@dataclass(slots=True, frozen=True)
class MetricPoint:
    """
    Normalized monitoring metric observation.

    Example:

        metric = "http.request.error_rate"
        value = 0.18
        unit = "ratio"
    """

    metric: str
    value: float
    timestamp: datetime
    unit: str | None = None
    service: str | None = None
    environment: str | None = None
    threshold: float | None = None
    source: str = "monitoring"
    labels: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class MonitoringAlert:
    """
    Normalized monitoring alert.

    An alert is an observation from a monitoring system, not automatically
    the root cause of an incident.
    """

    alert_id: str
    name: str
    status: str
    severity: str
    message: str
    timestamp: datetime
    service: str | None = None
    environment: str | None = None
    metric: str | None = None
    value: float | None = None
    threshold: float | None = None
    source: str = "monitoring"
    url: str | None = None
    labels: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class MonitoringErrorEvent:
    """
    Normalized application error-rate observation.
    """

    error_type: str
    message: str
    timestamp: datetime
    service: str | None = None
    environment: str | None = None
    count: int = 1
    rate: float | None = None
    source: str = "monitoring"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class MonitoringSnapshot:
    """
    Compact monitoring snapshot used by the investigation engine.

    Keeping this model bounded prevents huge monitoring responses from being
    passed unnecessarily into the LLM context.
    """

    collected_at: datetime
    service: str | None
    environment: str | None
    metrics: tuple[MetricPoint, ...] = ()
    alerts: tuple[MonitoringAlert, ...] = ()
    errors: tuple[MonitoringErrorEvent, ...] = ()

    @property
    def total_signals(self) -> int:
        """Return the total number of monitoring observations."""
        return len(self.metrics) + len(self.alerts) + len(self.errors)


# ============================================================================
# CLIENT
# ============================================================================


class MonitoringClient:
    """
    Async monitoring API client.

    The provider endpoint is optional. When no endpoint is configured, the
    client can still be used with `ingest_*` methods or demo data supplied by
    the service layer.

    A reusable httpx client is maintained for connection pooling.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        provider_name: str = "monitoring",
    ) -> None:
        self.settings = settings or get_settings()

        self.provider_name = provider_name.strip() or "monitoring"

        self.base_url = (
            base_url.rstrip("/")
            if base_url
            else None
        )

        self.api_key = api_key

        self._external_client = client is not None
        self._client = client

        if self._client is None and self.base_url:
            timeout = httpx.Timeout(
                timeout=self.settings.http_timeout_seconds,
                connect=self.settings.http_connect_timeout_seconds,
            )

            limits = httpx.Limits(
                max_connections=self.settings.http_max_connections,
                max_keepalive_connections=(
                    self.settings.http_max_keepalive_connections
                ),
            )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                headers=self._build_headers(),
            )

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    async def __aenter__(self) -> "MonitoringClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the internally owned HTTP client."""

        if self._client is not None and not self._external_client:
            await self._client.aclose()

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def _build_headers(self) -> dict[str, str]:
        """Build provider-neutral monitoring request headers."""

        headers = {
            "Accept": "application/json",
            "User-Agent": "TraceIQ/1.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _require_http_client(self) -> httpx.AsyncClient:
        """
        Return the configured HTTP client.

        Monitoring is intentionally optional, so configuration errors are
        explicit instead of silently causing misleading investigation results.
        """

        if self._client is None or not self.base_url:
            raise MonitoringConfigurationError(
                "Monitoring API is not configured. "
                "Provide a monitoring base URL before making remote requests."
            )

        return self._client

    # ========================================================================
    # LOW-LEVEL HTTP
    # ========================================================================

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """
        Execute a monitoring request.

        Provider-specific response parsing remains outside this method.
        """

        client = self._require_http_client()

        try:
            response = await client.request(
                method,
                endpoint,
                params=dict(params) if params else None,
                json=json,
            )

        except httpx.TimeoutException as exc:
            raise MonitoringTimeoutError(
                "Monitoring API request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise MonitoringAPIError(
                f"Monitoring API request failed: {exc}"
            ) from exc

        if response.status_code == 401:
            raise MonitoringAPIError(
                "Monitoring API authentication failed."
            )

        if response.status_code == 403:
            raise MonitoringAPIError(
                "Monitoring API access was forbidden."
            )

        if response.status_code == 404:
            raise MonitoringAPIError(
                f"Monitoring endpoint not found: {endpoint}"
            )

        if response.status_code >= 400:
            raise MonitoringAPIError(
                f"Monitoring API returned HTTP {response.status_code}."
            )

        if response.status_code == 204:
            return None

        try:
            return response.json()

        except ValueError as exc:
            raise MonitoringDataError(
                "Monitoring API returned invalid JSON."
            ) from exc

    # ========================================================================
    # METRICS
    # ========================================================================

    async def query_metrics(
        self,
        *,
        service: str | None = None,
        metric_names: Sequence[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[MetricPoint]:
        """
        Query metrics from the configured monitoring provider.

        The expected provider response is intentionally flexible. The parser
        accepts either:

            {"data": [...]}

        or:

            {"metrics": [...]}

        or a raw list.

        Providers with a different format can be adapted here without
        affecting the investigation layer.
        """

        limit = min(max(limit, 1), 1000)

        params: dict[str, Any] = {
            "limit": limit,
        }

        if service:
            params["service"] = service

        if metric_names:
            params["metrics"] = ",".join(metric_names)

        if start_time:
            params["start_time"] = _isoformat(start_time)

        if end_time:
            params["end_time"] = _isoformat(end_time)

        response = await self._request(
            "GET",
            "/metrics",
            params=params,
        )

        records = _extract_records(
            response,
            keys=("data", "metrics", "results"),
        )

        return [
            self._normalize_metric(record)
            for record in records
        ]

    # ========================================================================
    # ALERTS
    # ========================================================================

    async def get_alerts(
        self,
        *,
        service: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[MonitoringAlert]:
        """Retrieve normalized monitoring alerts."""

        limit = min(max(limit, 1), 1000)

        params: dict[str, Any] = {
            "limit": limit,
        }

        if service:
            params["service"] = service

        if start_time:
            params["start_time"] = _isoformat(start_time)

        if end_time:
            params["end_time"] = _isoformat(end_time)

        if status:
            params["status"] = status

        response = await self._request(
            "GET",
            "/alerts",
            params=params,
        )

        records = _extract_records(
            response,
            keys=("data", "alerts", "results"),
        )

        return [
            self._normalize_alert(record)
            for record in records
        ]

    # ========================================================================
    # ERRORS
    # ========================================================================

    async def get_errors(
        self,
        *,
        service: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[MonitoringErrorEvent]:
        """Retrieve normalized application errors."""

        limit = min(max(limit, 1), 1000)

        params: dict[str, Any] = {
            "limit": limit,
        }

        if service:
            params["service"] = service

        if start_time:
            params["start_time"] = _isoformat(start_time)

        if end_time:
            params["end_time"] = _isoformat(end_time)

        response = await self._request(
            "GET",
            "/errors",
            params=params,
        )

        records = _extract_records(
            response,
            keys=("data", "errors", "results"),
        )

        return [
            self._normalize_error(record)
            for record in records
        ]

    # ========================================================================
    # SNAPSHOT
    # ========================================================================

    async def collect_snapshot(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        metric_names: Sequence[str] | None = None,
        limit: int = 100,
    ) -> MonitoringSnapshot:
        """
        Collect a bounded monitoring snapshot.

        Metrics, alerts, and errors are fetched concurrently to reduce total
        investigation latency.
        """

        started = time.perf_counter()

        metrics_task = self.query_metrics(
            service=service,
            metric_names=metric_names,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        alerts_task = self.get_alerts(
            service=service,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        errors_task = self.get_errors(
            service=service,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        metrics, alerts, errors = await asyncio.gather(
            metrics_task,
            alerts_task,
            errors_task,
        )

        # The local variable is intentionally evaluated so latency can be
        # measured during debugging/profiling without adding it to the
        # public model.
        _ = time.perf_counter() - started

        return MonitoringSnapshot(
            collected_at=datetime.now(timezone.utc),
            service=service,
            environment=environment,
            metrics=tuple(metrics),
            alerts=tuple(alerts),
            errors=tuple(errors),
        )

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    def _normalize_metric(
        self,
        data: Mapping[str, Any],
    ) -> MetricPoint:
        """Normalize a provider metric record."""

        metric = _first_string(
            data,
            "metric",
            "metric_name",
            "name",
        )

        if not metric:
            raise MonitoringDataError(
                "Monitoring metric is missing its name."
            )

        value = _to_float(
            data.get("value"),
        )

        if value is None:
            raise MonitoringDataError(
                f"Monitoring metric '{metric}' has an invalid value."
            )

        timestamp = _parse_datetime(
            data.get("timestamp")
            or data.get("time")
            or data.get("observed_at")
        )

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        labels = _normalize_string_mapping(
            data.get("labels"),
        )

        metadata = _normalize_metadata(data)

        return MetricPoint(
            metric=metric,
            value=value,
            timestamp=timestamp,
            unit=_first_string(data, "unit"),
            service=_first_string(data, "service"),
            environment=_first_string(data, "environment"),
            threshold=_to_float(data.get("threshold")),
            source=self.provider_name,
            labels=labels,
            metadata=metadata,
        )

    def _normalize_alert(
        self,
        data: Mapping[str, Any],
    ) -> MonitoringAlert:
        """Normalize a provider alert record."""

        alert_id = _first_string(
            data,
            "id",
            "alert_id",
            "identifier",
        )

        name = _first_string(
            data,
            "name",
            "title",
            "alert_name",
        )

        if not alert_id:
            raise MonitoringDataError(
                "Monitoring alert is missing an ID."
            )

        if not name:
            raise MonitoringDataError(
                f"Monitoring alert '{alert_id}' is missing a name."
            )

        timestamp = _parse_datetime(
            data.get("timestamp")
            or data.get("time")
            or data.get("created_at")
        )

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        value = _to_float(data.get("value"))
        threshold = _to_float(data.get("threshold"))

        return MonitoringAlert(
            alert_id=alert_id,
            name=name,
            status=_first_string(
                data,
                "status",
            ) or "firing",
            severity=_first_string(
                data,
                "severity",
                "priority",
            ) or "medium",
            message=_first_string(
                data,
                "message",
                "description",
            ) or name,
            timestamp=timestamp,
            service=_first_string(data, "service"),
            environment=_first_string(data, "environment"),
            metric=_first_string(
                data,
                "metric",
                "metric_name",
            ),
            value=value,
            threshold=threshold,
            source=self.provider_name,
            url=_first_string(
                data,
                "url",
                "html_url",
            ),
            labels=_normalize_string_mapping(
                data.get("labels"),
            ),
            metadata=_normalize_metadata(data),
        )

    def _normalize_error(
        self,
        data: Mapping[str, Any],
    ) -> MonitoringErrorEvent:
        """Normalize a provider error record."""

        error_type = _first_string(
            data,
            "error_type",
            "type",
            "exception",
        )

        message = _first_string(
            data,
            "message",
            "error",
            "description",
        )

        if not error_type:
            error_type = "UnknownError"

        if not message:
            message = "Unknown monitoring error"

        timestamp = _parse_datetime(
            data.get("timestamp")
            or data.get("time")
            or data.get("created_at")
        )

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        count = _to_int(
            data.get("count")
            or data.get("occurrences")
        ) or 1

        return MonitoringErrorEvent(
            error_type=error_type,
            message=message,
            timestamp=timestamp,
            service=_first_string(data, "service"),
            environment=_first_string(data, "environment"),
            count=max(count, 1),
            rate=_to_float(
                data.get("rate")
                or data.get("error_rate")
            ),
            source=self.provider_name,
            metadata=_normalize_metadata(data),
        )


# ============================================================================
# DEMO / IN-MEMORY MONITORING
# ============================================================================


class InMemoryMonitoringClient:
    """
    Deterministic monitoring client for TraceIQ demo mode and unit tests.

    This allows the hackathon demonstration to run without requiring a live
    monitoring provider.

    It intentionally implements the same high-level behavior needed by the
    investigation service without pretending the data came from a real
    external provider.
    """

    def __init__(
        self,
        *,
        metrics: Sequence[MetricPoint] | None = None,
        alerts: Sequence[MonitoringAlert] | None = None,
        errors: Sequence[MonitoringErrorEvent] | None = None,
    ) -> None:
        self._metrics = tuple(metrics or ())
        self._alerts = tuple(alerts or ())
        self._errors = tuple(errors or ())

    async def collect_snapshot(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        metric_names: Sequence[str] | None = None,
        limit: int = 100,
    ) -> MonitoringSnapshot:
        """Return deterministic filtered monitoring data."""

        metric_name_set = set(metric_names or ())

        metrics = [
            item
            for item in self._metrics
            if (
                not service
                or item.service is None
                or item.service == service
            )
            and (
                not metric_name_set
                or item.metric in metric_name_set
            )
            and _within_window(
                item.timestamp,
                start_time,
                end_time,
            )
        ][:limit]

        alerts = [
            item
            for item in self._alerts
            if (
                not service
                or item.service is None
                or item.service == service
            )
            and _within_window(
                item.timestamp,
                start_time,
                end_time,
            )
        ][:limit]

        errors = [
            item
            for item in self._errors
            if (
                not service
                or item.service is None
                or item.service == service
            )
            and _within_window(
                item.timestamp,
                start_time,
                end_time,
            )
        ][:limit]

        return MonitoringSnapshot(
            collected_at=datetime.now(timezone.utc),
            service=service,
            environment=environment,
            metrics=tuple(metrics),
            alerts=tuple(alerts),
            errors=tuple(errors),
        )


# ============================================================================
# HELPERS
# ============================================================================


def _extract_records(
    response: Any,
    *,
    keys: Sequence[str],
) -> list[Mapping[str, Any]]:
    """Extract a list of records from common provider response formats."""

    if isinstance(response, list):
        records = response

    elif isinstance(response, dict):
        records = None

        for key in keys:
            candidate = response.get(key)

            if isinstance(candidate, list):
                records = candidate
                break

        if records is None:
            raise MonitoringDataError(
                "Monitoring response does not contain a supported record list."
            )

    else:
        raise MonitoringDataError(
            "Monitoring response has an unsupported format."
        )

    normalized: list[Mapping[str, Any]] = []

    for record in records:
        if isinstance(record, Mapping):
            normalized.append(record)

    return normalized


def _first_string(
    data: Mapping[str, Any],
    *keys: str,
) -> str | None:
    """Return the first non-empty string among candidate keys."""

    for key in keys:
        value = data.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _to_float(value: Any) -> float | None:
    """Safely convert a value to float."""

    if isinstance(value, bool):
        return None

    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    """Safely convert a value to int."""

    if isinstance(value, bool):
        return None

    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    """Safely parse an ISO-8601 datetime."""

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed

    except ValueError:
        return None


def _isoformat(value: datetime) -> str:
    """Convert a datetime to an API-safe ISO-8601 representation."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.isoformat()


def _normalize_string_mapping(
    value: Any,
) -> dict[str, str]:
    """Normalize provider labels into string key/value pairs."""

    if not isinstance(value, Mapping):
        return {}

    result: dict[str, str] = {}

    for key, item in value.items():
        if item is None:
            continue

        result[str(key)] = str(item)

    return result


def _normalize_metadata(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Preserve useful provider metadata while excluding fields already
    normalized into the public model.
    """

    normalized_keys = {
        "metric",
        "metric_name",
        "name",
        "value",
        "timestamp",
        "time",
        "observed_at",
        "unit",
        "service",
        "environment",
        "threshold",
        "labels",
        "id",
        "alert_id",
        "identifier",
        "alert_name",
        "status",
        "severity",
        "priority",
        "message",
        "description",
        "metric",
        "url",
        "html_url",
        "error_type",
        "type",
        "exception",
        "error",
        "count",
        "occurrences",
        "rate",
        "error_rate",
        "created_at",
    }

    return {
        str(key): value
        for key, value in data.items()
        if key not in normalized_keys
    }


def _within_window(
    timestamp: datetime,
    start_time: datetime | None,
    end_time: datetime | None,
) -> bool:
    """Return whether a timestamp falls within an optional time window."""

    if start_time is not None:
        if timestamp < start_time:
            return False

    if end_time is not None:
        if timestamp > end_time:
            return False

    return True


# ============================================================================
# FACTORY
# ============================================================================


def create_monitoring_client(
    settings: Settings | None = None,
    *,
    client: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    provider_name: str = "monitoring",
) -> MonitoringClient:
    """
    Construct a monitoring client.

    `base_url` and `api_key` are injectable so the same client can support
    different monitoring providers without changing the service layer.
    """

    return MonitoringClient(
        settings=settings or get_settings(),
        client=client,
        base_url=base_url,
        api_key=api_key,
        provider_name=provider_name,
    )


__all__ = [
    "MonitoringClient",
    "InMemoryMonitoringClient",
    "MonitoringIntegrationError",
    "MonitoringConfigurationError",
    "MonitoringAPIError",
    "MonitoringTimeoutError",
    "MonitoringDataError",
    "MetricPoint",
    "MonitoringAlert",
    "MonitoringErrorEvent",
    "MonitoringSnapshot",
    "create_monitoring_client",
]