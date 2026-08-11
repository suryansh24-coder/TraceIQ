"""
TraceIQ - Investigation Schemas

Defines the request/response contracts for TraceIQ's investigation engine.

Primary flow:

    InvestigationRequest
            ↓
       Orchestrator
            ↓
    Evidence Collection
            ↓
    Evidence Validation
            ↓
    Timeline Construction
            ↓
    Root Cause Analysis
            ↓
    Confidence Assessment
            ↓
    Recommendations
            ↓
    InvestigationResponse

This module contains schemas only. Business logic belongs in services.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.schemas.common import (
    BaseTraceIQModel,
    ConfidenceLevel,
    Severity,
    Status,
)
from app.schemas.evidence import Evidence, TimelineEvent


# ============================================================================
# INVESTIGATION REQUEST
# ============================================================================


class InvestigationRequest(BaseTraceIQModel):
    """
    Request submitted by an engineer to start an investigation.

    The query is the primary input. Additional fields provide optional
    context that can significantly improve investigation accuracy.
    """

    query: str = Field(
        min_length=3,
        max_length=20000,
        description="Natural-language investigation request.",
    )

    incident_id: str | None = Field(
        default=None,
        max_length=500,
        description="Known incident identifier.",
    )

    service: str | None = Field(
        default=None,
        max_length=500,
        description="Service involved in the incident.",
    )

    repository: str | None = Field(
        default=None,
        max_length=500,
        description="Repository associated with the investigation.",
    )

    severity: Severity | None = Field(
        default=None,
        description="Known incident severity.",
    )

    conversation_id: str | None = Field(
        default=None,
        max_length=500,
        description="Conversation identifier for investigation continuity.",
    )

    time_window_minutes: int | None = Field(
        default=None,
        ge=1,
        le=10080,
        description="Historical window to inspect, in minutes.",
    )

    include_historical_incidents: bool = Field(
        default=True,
        description="Whether historical incidents should be considered.",
    )

    include_code_changes: bool = Field(
        default=True,
        description="Whether recent code changes should be inspected.",
    )

    include_deployments: bool = Field(
        default=True,
        description="Whether recent deployments should be inspected.",
    )

    include_monitoring: bool = Field(
        default=True,
        description="Whether monitoring signals should be inspected.",
    )

    include_rag: bool = Field(
        default=True,
        description="Whether the knowledge/RAG layer should be queried.",
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured investigation context.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Normalize and validate the investigation query."""
        value = value.strip()

        if not value:
            raise ValueError("Investigation query cannot be empty.")

        return value


# ============================================================================
# INVESTIGATION STEP
# ============================================================================


class InvestigationStep(BaseTraceIQModel):
    """
    Represents one execution step performed by the investigation orchestrator.
    """

    step_id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique step identifier.",
    )

    name: str = Field(
        min_length=1,
        max_length=500,
        description="Human-readable step name.",
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Description of the step.",
    )

    status: Status = Field(
        default=Status.PENDING,
        description="Execution status.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Step start time.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Step completion time.",
    )

    duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="Step execution duration.",
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence produced or consumed by the step.",
    )

    error: str | None = Field(
        default=None,
        max_length=10000,
        description="Error message when the step fails.",
    )


# ============================================================================
# LIKELY ROOT CAUSE
# ============================================================================


class LikelyCause(BaseTraceIQModel):
    """
    Hypothesized root cause.

    This is explicitly a hypothesis rather than a guaranteed fact.
    Supporting and contradicting evidence should determine confidence.
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique identifier for the root-cause candidate.",
    )

    cause: str = Field(
        min_length=1,
        max_length=2000,
        description="Hypothesized root cause.",
    )

    explanation: str = Field(
        min_length=1,
        max_length=20000,
        description="Evidence-based explanation.",
    )

    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this cause.",
    )

    contradicting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence contradicting this cause.",
    )

    confidence: ConfidenceLevel = Field(
        description="Human-readable confidence level.",
    )

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Numeric confidence score.",
    )

    affected_services: list[str] = Field(
        default_factory=list,
        description="Services potentially affected by the cause.",
    )

    affected_files: list[str] = Field(
        default_factory=list,
        description="Potentially affected source files.",
    )

    related_commits: list[str] = Field(
        default_factory=list,
        description="Relevant commit SHAs.",
    )


# ============================================================================
# RECOMMENDATION
# ============================================================================


class Recommendation(BaseTraceIQModel):
    """
    Actionable engineering recommendation.

    Recommendations describe what should be done. They do not automatically
    execute production-changing actions.
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique recommendation identifier.",
    )

    action: str = Field(
        min_length=1,
        max_length=5000,
        description="Recommended engineering action.",
    )

    reason: str = Field(
        min_length=1,
        max_length=10000,
        description="Reason the action is recommended.",
    )

    priority: Severity = Field(
        default=Severity.MEDIUM,
        description="Recommendation priority.",
    )

    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence supporting the recommendation.",
    )

    expected_impact: str | None = Field(
        default=None,
        max_length=5000,
        description="Expected outcome if the recommendation is followed.",
    )

    risk: str | None = Field(
        default=None,
        max_length=5000,
        description="Potential risk associated with the recommendation.",
    )

    automated: bool = Field(
        default=False,
        description="Whether TraceIQ can potentially automate this action.",
    )

    requires_approval: bool = Field(
        default=True,
        description="Whether human approval is required.",
    )


# ============================================================================
# CONFIDENCE ASSESSMENT
# ============================================================================


class ConfidenceAssessment(BaseTraceIQModel):
    """
    Overall confidence in an investigation result.

    The score is numeric while level provides a human-readable classification.
    """

    level: ConfidenceLevel = Field(
        description="Overall confidence level.",
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized confidence score from 0 to 1.",
    )

    basis: list[str] = Field(
        default_factory=list,
        description="Reasons supporting the confidence assessment.",
    )

    supporting_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of supporting evidence items.",
    )

    conflicting_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of conflicting evidence items.",
    )

    source_count: int = Field(
        default=0,
        ge=0,
        description="Number of independent sources contributing evidence.",
    )

    validated_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of evidence items that passed validation.",
    )


# ============================================================================
# INVESTIGATION METADATA
# ============================================================================


class InvestigationMetadata(BaseTraceIQModel):
    """
    Operational metadata about how an investigation was executed.

    This information is useful for observability, debugging, performance
    analysis, and hackathon demonstrations.
    """

    started_at: datetime | None = Field(
        default=None,
        description="Investigation start time.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Investigation completion time.",
    )

    duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="Total investigation duration.",
    )

    model: str | None = Field(
        default=None,
        description="LLM model used.",
    )

    llm_provider: str | None = Field(
        default=None,
        description="LLM provider used.",
    )

    evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of evidence items collected.",
    )

    validated_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of validated evidence items.",
    )

    source_count: int = Field(
        default=0,
        ge=0,
        description="Number of external sources consulted.",
    )

    steps_completed: int = Field(
        default=0,
        ge=0,
        description="Number of completed investigation steps.",
    )

    demo_mode: bool = Field(
        default=False,
        description="Whether the result was generated using demo data.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings generated during investigation.",
    )


# ============================================================================
# INVESTIGATION RESPONSE
# ============================================================================


class InvestigationResponse(BaseTraceIQModel):
    """
    Complete result returned by the TraceIQ investigation engine.

    The response is intentionally evidence-oriented:
    conclusions reference evidence IDs rather than relying on unsupported
    natural-language claims.
    """

    request_id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique request/investigation identifier.",
    )

    incident_id: str | None = Field(
        default=None,
        max_length=500,
        description="Related incident identifier.",
    )

    service: str | None = Field(
        default=None,
        max_length=500,
        description="Affected service.",
    )

    repository: str | None = Field(
        default=None,
        max_length=500,
        description="Associated repository.",
    )

    status: Status = Field(
        default=Status.COMPLETED,
        description="Investigation lifecycle status.",
    )

    severity: Severity | None = Field(
        default=None,
        description="Incident severity.",
    )

    summary: str = Field(
        min_length=1,
        max_length=30000,
        description="Evidence-grounded high-level investigation summary.",
    )

    timeline: list[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological incident timeline.",
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Collected and normalized evidence.",
    )

    likely_causes: list[LikelyCause] = Field(
        default_factory=list,
        description="Ranked root-cause hypotheses.",
    )

    confidence: ConfidenceAssessment = Field(
        description="Overall investigation confidence.",
    )

    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Actionable engineering recommendations.",
    )

    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Useful questions for further investigation.",
    )

    sources: list[str] = Field(
        default_factory=list,
        description="Distinct source systems consulted.",
    )

    steps: list[InvestigationStep] = Field(
        default_factory=list,
        description="Investigation execution steps.",
    )

    processing_metadata: InvestigationMetadata = Field(
        default_factory=InvestigationMetadata,
        description="Operational investigation metadata.",
    )


# ============================================================================
# INVESTIGATION STATUS RESPONSE
# ============================================================================


class InvestigationStatusResponse(BaseTraceIQModel):
    """Lightweight response for checking investigation progress."""

    request_id: str = Field(
        min_length=1,
        max_length=500,
    )

    status: Status = Field(
        description="Current investigation status.",
    )

    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized investigation progress.",
    )

    current_step: str | None = Field(
        default=None,
        max_length=500,
        description="Currently executing investigation step.",
    )

    completed_steps: int = Field(
        default=0,
        ge=0,
    )

    total_steps: int = Field(
        default=0,
        ge=0,
    )

    message: str | None = Field(
        default=None,
        max_length=5000,
    )


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "InvestigationRequest",
    "InvestigationStep",
    "LikelyCause",
    "Recommendation",
    "ConfidenceAssessment",
    "InvestigationMetadata",
    "InvestigationResponse",
    "InvestigationStatusResponse",
]