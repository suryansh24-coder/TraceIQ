"""
TraceIQ - Common Pydantic Schemas

Shared enums, base models, pagination models, API response models,
and common validation primitives used throughout the backend.

This module must remain lightweight and dependency-free from services,
integrations, database layers, and API routers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# ENUMS
# ============================================================================


class Severity(str, Enum):
    """Severity assigned to an incident or engineering event."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Human-readable confidence classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    """Generic lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HealthStatus(str, Enum):
    """Service health state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================================================
# BASE MODEL
# ============================================================================


class BaseTraceIQModel(BaseModel):
    """
    Base Pydantic model used across TraceIQ.

    Pydantic v2 configuration:
    - Allows population by field name or alias.
    - Ignores unknown fields for forward compatibility.
    - Validates values when models are constructed.
    - Produces consistent JSON-compatible output.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


# ============================================================================
# PAGINATION
# ============================================================================


class PaginationParams(BaseTraceIQModel):
    """Standard pagination parameters."""

    page: int = Field(
        default=1,
        ge=1,
        description="1-based page number.",
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of records returned per page.",
    )

    @property
    def offset(self) -> int:
        """Calculate database/query offset."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseTraceIQModel):
    """Metadata returned with paginated responses."""

    page: int = Field(
        ge=1,
        description="Current page number.",
    )

    page_size: int = Field(
        ge=1,
        description="Number of records per page.",
    )

    total: int = Field(
        ge=0,
        description="Total number of available records.",
    )

    total_pages: int = Field(
        ge=0,
        description="Total number of pages.",
    )

    has_next: bool = Field(
        description="Whether another page exists.",
    )

    has_previous: bool = Field(
        description="Whether a previous page exists.",
    )


# ============================================================================
# API RESPONSE MODELS
# ============================================================================


class APIMessage(BaseTraceIQModel):
    """Simple API status/message payload."""

    message: str = Field(
        min_length=1,
        description="Human-readable message.",
    )


class APIError(BaseTraceIQModel):
    """Normalized API error representation."""

    code: str = Field(
        min_length=1,
        description="Machine-readable error code.",
    )

    message: str = Field(
        min_length=1,
        description="Human-readable error message.",
    )

    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured error details.",
    )

    request_id: str | None = Field(
        default=None,
        description="Request identifier useful for troubleshooting.",
    )


class APIResponse(BaseTraceIQModel, Generic[TypeVar("T")]):
    """
    Generic API response envelope.

    Example:

        {
            "success": true,
            "data": {...},
            "message": "Investigation completed"
        }
    """

    success: bool = Field(
        default=True,
        description="Whether the operation succeeded.",
    )

    data: Any | None = Field(
        default=None,
        description="Response payload.",
    )

    message: str | None = Field(
        default=None,
        description="Optional human-readable status message.",
    )

    error: APIError | None = Field(
        default=None,
        description="Structured error information.",
    )


# ============================================================================
# PAGINATED RESPONSE
# ============================================================================


T = TypeVar("T")


class PaginatedResponse(BaseTraceIQModel, Generic[T]):
    """Generic paginated API response."""

    success: bool = Field(
        default=True,
        description="Whether the operation succeeded.",
    )

    data: list[T] = Field(
        default_factory=list,
        description="Records returned by the request.",
    )

    pagination: PaginationMeta = Field(
        description="Pagination metadata.",
    )


# ============================================================================
# IDENTIFIERS
# ============================================================================


class ResourceIdentifier(BaseTraceIQModel):
    """Common identifier representation for TraceIQ resources."""

    id: str = Field(
        min_length=1,
        description="Unique resource identifier.",
    )


# ============================================================================
# HEALTH
# ============================================================================


class ComponentHealth(BaseTraceIQModel):
    """Health information for an individual backend component."""

    name: str = Field(
        min_length=1,
        description="Component name.",
    )

    status: HealthStatus = Field(
        description="Current component health.",
    )

    latency_ms: float | None = Field(
        default=None,
        ge=0,
        description="Observed health-check latency in milliseconds.",
    )

    message: str | None = Field(
        default=None,
        description="Optional component health message.",
    )


class HealthResponse(BaseTraceIQModel):
    """TraceIQ health endpoint response."""

    status: HealthStatus = Field(
        description="Overall application health.",
    )

    version: str = Field(
        min_length=1,
        description="Running TraceIQ version.",
    )

    environment: str = Field(
        min_length=1,
        description="Application environment.",
    )

    components: list[ComponentHealth] = Field(
        default_factory=list,
        description="Individual component health states.",
    )


# ============================================================================
# UTILITY
# ============================================================================


class TimestampedModel(BaseTraceIQModel):
    """
    Base model for objects carrying creation/update timestamps.

    Timestamp values are represented as ISO-8601 strings at the schema layer
    to keep this shared module independent of database implementations.
    """

    created_at: str | None = Field(
        default=None,
        description="Creation timestamp in ISO-8601 format.",
    )

    updated_at: str | None = Field(
        default=None,
        description="Last update timestamp in ISO-8601 format.",
    )


__all__ = [
    "Severity",
    "ConfidenceLevel",
    "Status",
    "HealthStatus",
    "BaseTraceIQModel",
    "PaginationParams",
    "PaginationMeta",
    "APIMessage",
    "APIError",
    "APIResponse",
    "PaginatedResponse",
    "ResourceIdentifier",
    "ComponentHealth",
    "HealthResponse",
    "TimestampedModel",
]