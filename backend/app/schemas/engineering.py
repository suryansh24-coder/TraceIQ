"""
TraceIQ - Engineering Domain Schemas

Pydantic models representing engineering and operational data used by
TraceIQ investigations.

This module contains:
- Incident information
- Repository information
- Commit/change information
- Deployment information
- Monitoring signals
- Error information
- Service information

No business logic, API calls, database operations, or LLM logic should
be placed in this module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, HttpUrl

from app.schemas.common import (
    BaseTraceIQModel,
    ConfidenceLevel,
    Severity,
    Status,
)


# ============================================================================
# REPOSITORY
# ============================================================================


class RepositoryRef(BaseTraceIQModel):
    """
    Reference to a GitHub repository.

    Example:
        owner = "acme"
        name = "payments-api"
    """

    owner: str = Field(
        min_length=1,
        max_length=100,
        description="GitHub repository owner or organization.",
    )

    name: str = Field(
        min_length=1,
        max_length=200,
        description="GitHub repository name.",
    )

    branch: str = Field(
        default="main",
        min_length=1,
        max_length=255,
        description="Relevant repository branch.",
    )

    url: HttpUrl | None = Field(
        default=None,
        description="Repository URL.",
    )

    @property
    def full_name(self) -> str:
        """Return the standard GitHub owner/repository identifier."""
        return f"{self.owner}/{self.name}"


# ============================================================================
# SERVICE
# ============================================================================


class ServiceRef(BaseTraceIQModel):
    """Application/service involved in an engineering incident."""

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Service name.",
    )

    environment: str = Field(
        default="production",
        min_length=1,
        max_length=100,
        description="Deployment environment.",
    )

    version: str | None = Field(
        default=None,
        max_length=200,
        description="Currently deployed service version.",
    )

    repository: RepositoryRef | None = Field(
        default=None,
        description="Repository containing the service source code.",
    )


# ============================================================================
# ERROR
# ============================================================================


class ErrorEvent(BaseTraceIQModel):
    """Normalized application/runtime error."""

    error_type: str = Field(
        min_length=1,
        max_length=500,
        description="Exception or error type.",
    )

    message: str = Field(
        min_length=1,
        max_length=10000,
        description="Error message.",
    )

    stack_trace: str | None = Field(
        default=None,
        max_length=50000,
        description="Optional stack trace.",
    )

    error_code: str | None = Field(
        default=None,
        max_length=200,
        description="Application or infrastructure error code.",
    )

    source: str | None = Field(
        default=None,
        max_length=500,
        description="Originating component/module.",
    )

    timestamp: datetime | None = Field(
        default=None,
        description="Time at which the error occurred.",
    )

    occurrence_count: int = Field(
        default=1,
        ge=1,
        description="Number of observed occurrences represented by this event.",
    )


# ============================================================================
# COMMIT / CODE CHANGE
# ============================================================================


class CommitRef(BaseTraceIQModel):
    """Git commit associated with an incident or deployment."""

    sha: str = Field(
        min_length=7,
        max_length=64,
        description="Git commit SHA.",
    )

    message: str = Field(
        min_length=1,
        max_length=10000,
        description="Commit message.",
    )

    author: str | None = Field(
        default=None,
        max_length=500,
        description="Commit author.",
    )

    author_email: str | None = Field(
        default=None,
        max_length=500,
        description="Commit author email when available.",
    )

    timestamp: datetime | None = Field(
        default=None,
        description="Commit timestamp.",
    )

    url: HttpUrl | None = Field(
        default=None,
        description="GitHub commit URL.",
    )

    files_changed: list[str] = Field(
        default_factory=list,
        description="Files changed by this commit.",
    )

    additions: int = Field(
        default=0,
        ge=0,
        description="Number of added lines.",
    )

    deletions: int = Field(
        default=0,
        ge=0,
        description="Number of deleted lines.",
    )


# ============================================================================
# DEPLOYMENT
# ============================================================================


class DeploymentEvent(BaseTraceIQModel):
    """Deployment event associated with an incident."""

    deployment_id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique deployment identifier.",
    )

    service: str = Field(
        min_length=1,
        max_length=200,
        description="Service being deployed.",
    )

    environment: str = Field(
        default="production",
        min_length=1,
        max_length=100,
        description="Deployment environment.",
    )

    status: Status = Field(
        default=Status.COMPLETED,
        description="Deployment lifecycle status.",
    )

    commit: CommitRef | None = Field(
        default=None,
        description="Commit deployed.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Deployment start time.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Deployment completion time.",
    )

    actor: str | None = Field(
        default=None,
        max_length=500,
        description="User or automation that initiated the deployment.",
    )

    url: HttpUrl | None = Field(
        default=None,
        description="Deployment/run URL.",
    )


# ============================================================================
# MONITORING SIGNAL
# ============================================================================


class MonitoringSignal(BaseTraceIQModel):
    """
    Observability signal used during an investigation.

    Examples:
    - HTTP 5xx spike
    - latency increase
    - CPU saturation
    - error-rate increase
    """

    metric: str = Field(
        min_length=1,
        max_length=500,
        description="Metric or signal name.",
    )

    value: float | int | str = Field(
        description="Observed metric value.",
    )

    threshold: float | int | None = Field(
        default=None,
        description="Configured threshold, when available.",
    )

    unit: str | None = Field(
        default=None,
        max_length=100,
        description="Metric unit.",
    )

    timestamp: datetime | None = Field(
        default=None,
        description="Time of the observation.",
    )

    source: str | None = Field(
        default=None,
        max_length=500,
        description="Monitoring system that produced the signal.",
    )

    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Severity associated with the signal.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional monitoring metadata.",
    )


# ============================================================================
# INCIDENT
# ============================================================================


class Incident(BaseTraceIQModel):
    """
    Core engineering incident representation.

    This is intentionally provider-agnostic. GitHub, monitoring platforms,
    logs, and LLM services can contribute information to an Incident without
    coupling this schema to a specific external vendor.
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique incident identifier.",
    )

    title: str = Field(
        min_length=1,
        max_length=1000,
        description="Short incident title.",
    )

    description: str | None = Field(
        default=None,
        max_length=20000,
        description="Detailed incident description.",
    )

    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Incident severity.",
    )

    status: Status = Field(
        default=Status.PENDING,
        description="Current incident investigation status.",
    )

    service: ServiceRef | None = Field(
        default=None,
        description="Affected service.",
    )

    repository: RepositoryRef | None = Field(
        default=None,
        description="Repository associated with the incident.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Approximate incident start time.",
    )

    detected_at: datetime | None = Field(
        default=None,
        description="Time at which the incident was detected.",
    )

    resolved_at: datetime | None = Field(
        default=None,
        description="Time at which the incident was resolved.",
    )

    errors: list[ErrorEvent] = Field(
        default_factory=list,
        description="Observed errors.",
    )

    monitoring_signals: list[MonitoringSignal] = Field(
        default_factory=list,
        description="Monitoring signals associated with the incident.",
    )

    deployments: list[DeploymentEvent] = Field(
        default_factory=list,
        description="Recent deployments relevant to the incident.",
    )

    commits: list[CommitRef] = Field(
        default_factory=list,
        description="Potentially relevant commits.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional incident metadata.",
    )


# ============================================================================
# ENGINEERING CONTEXT
# ============================================================================


class EngineeringContext(BaseTraceIQModel):
    """
    Consolidated engineering context supplied to the investigation engine.

    This model is useful for combining information collected from GitHub,
    monitoring systems, deployment systems, and incident reports before
    passing the context into the orchestration layer.
    """

    incident: Incident

    services: list[ServiceRef] = Field(
        default_factory=list,
        description="Services relevant to the investigation.",
    )

    recent_commits: list[CommitRef] = Field(
        default_factory=list,
        description="Recent commits considered during investigation.",
    )

    recent_deployments: list[DeploymentEvent] = Field(
        default_factory=list,
        description="Recent deployments considered during investigation.",
    )

    monitoring_signals: list[MonitoringSignal] = Field(
        default_factory=list,
        description="Collected monitoring signals.",
    )

    errors: list[ErrorEvent] = Field(
        default_factory=list,
        description="Collected errors.",
    )

    source_count: int = Field(
        default=0,
        ge=0,
        description="Number of external/context sources contributing evidence.",
    )

    collection_timestamp: datetime | None = Field(
        default=None,
        description="Time at which engineering context was collected.",
    )


# ============================================================================
# ROOT-CAUSE CANDIDATE
# ============================================================================


class RootCauseCandidate(BaseTraceIQModel):
    """
    Candidate root cause generated from collected engineering evidence.

    This is a candidate—not a confirmed root cause. Confirmation happens
    through the evidence validation and confidence layers.
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique candidate identifier.",
    )

    title: str = Field(
        min_length=1,
        max_length=1000,
        description="Short candidate root-cause title.",
    )

    explanation: str = Field(
        min_length=1,
        max_length=20000,
        description="Reasoning behind the candidate.",
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Numeric confidence score.",
    )

    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.LOW,
        description="Human-readable confidence level.",
    )

    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers supporting this candidate.",
    )

    contradicting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers contradicting this candidate.",
    )

    affected_services: list[str] = Field(
        default_factory=list,
        description="Services potentially affected by this cause.",
    )

    affected_files: list[str] = Field(
        default_factory=list,
        description="Potentially affected source files.",
    )

    related_commits: list[str] = Field(
        default_factory=list,
        description="Related commit SHAs.",
    )


# ============================================================================
# ENGINEERING RECOMMENDATION
# ============================================================================


class EngineeringRecommendation(BaseTraceIQModel):
    """
    Action recommended by TraceIQ after investigation.

    The recommendation itself is not an execution command. Actual actions
    must pass through the appropriate integration and authorization layer.
    """

    title: str = Field(
        min_length=1,
        max_length=1000,
        description="Recommendation title.",
    )

    description: str = Field(
        min_length=1,
        max_length=20000,
        description="Recommended engineering action.",
    )

    priority: Severity = Field(
        default=Severity.MEDIUM,
        description="Recommendation priority.",
    )

    rationale: str | None = Field(
        default=None,
        max_length=20000,
        description="Reasoning behind the recommendation.",
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this recommendation.",
    )

    automated: bool = Field(
        default=False,
        description="Whether this recommendation can be safely automated.",
    )

    requires_approval: bool = Field(
        default=True,
        description="Whether human approval is required before execution.",
    )


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "RepositoryRef",
    "ServiceRef",
    "ErrorEvent",
    "CommitRef",
    "DeploymentEvent",
    "MonitoringSignal",
    "Incident",
    "EngineeringContext",
    "RootCauseCandidate",
    "EngineeringRecommendation",
]