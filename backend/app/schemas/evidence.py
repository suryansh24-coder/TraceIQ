"""
TraceIQ - Evidence Schemas

Defines the normalized evidence model used throughout the investigation
pipeline.

Evidence is the foundation of TraceIQ's reasoning system:

    External Sources
          ↓
    Evidence Collection
          ↓
    Evidence Normalization
          ↓
    Evidence Validation
          ↓
    Confidence Scoring
          ↓
    Root-Cause Analysis
          ↓
    Recommendations / Report

The models in this module intentionally remain provider-agnostic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, HttpUrl

from app.schemas.common import (
    BaseTraceIQModel,
    ConfidenceLevel,
    Severity,
)


# ============================================================================
# ENUMS
# ============================================================================


class EvidenceSource(str, Enum):
    """Supported categories of external evidence sources."""

    GITHUB = "github"
    GITHUB_ACTIONS = "github_actions"
    MONITORING = "monitoring"
    LOGS = "logs"
    DATABASE = "database"
    QDRANT = "qdrant"
    RUNBOOK = "runbook"
    INCIDENT = "incident"
    DEPLOYMENT = "deployment"
    USER_REPORT = "user_report"
    SYSTEM = "system"
    DEMO = "demo"


class EvidenceType(str, Enum):
    """Type of engineering evidence."""

    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    DEPLOYMENT = "deployment"
    CI_RUN = "ci_run"
    ALERT = "alert"
    LOG = "log"
    ERROR = "error"
    METRIC = "metric"
    TRACE = "trace"
    INCIDENT = "incident"
    RUNBOOK = "runbook"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    CODE = "code"
    USER_REPORT = "user_report"
    HISTORICAL_INCIDENT = "historical_incident"
    OTHER = "other"


class EvidenceValidity(str, Enum):
    """Validation state of an evidence item."""

    UNVERIFIED = "unverified"
    VALID = "valid"
    INVALID = "invalid"
    STALE = "stale"
    CONFLICTING = "conflicting"


class EvidenceStrength(str, Enum):
    """Human-readable strength of an evidence item."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONCLUSIVE = "conclusive"


# ============================================================================
# EVIDENCE SOURCE REFERENCE
# ============================================================================


class EvidenceSourceRef(BaseTraceIQModel):
    """
    Identifies exactly where evidence originated.

    Keeping source identity separate from the evidence content allows us to
    trace an LLM conclusion back to the original system.
    """

    provider: EvidenceSource = Field(
        description="System that produced the evidence.",
    )

    source_id: str | None = Field(
        default=None,
        max_length=1000,
        description="Provider-specific identifier.",
    )

    url: HttpUrl | None = Field(
        default=None,
        description="Direct URL to the original evidence.",
    )

    repository: str | None = Field(
        default=None,
        max_length=500,
        description="Repository associated with the evidence.",
    )

    environment: str | None = Field(
        default=None,
        max_length=100,
        description="Environment associated with the evidence.",
    )

    retrieved_at: datetime | None = Field(
        default=None,
        description="Time at which TraceIQ retrieved this evidence.",
    )


# ============================================================================
# EVIDENCE
# ============================================================================


class Evidence(BaseTraceIQModel):
    """
    Normalized piece of evidence used by the TraceIQ investigation engine.

    An Evidence object should represent one meaningful, independently
    referenceable observation.

    Examples:
    - A GitHub commit
    - A failed CI run
    - A monitoring alert
    - A production error
    - A relevant runbook section
    - A historical incident
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Globally unique evidence identifier.",
    )

    source: EvidenceSource = Field(
        description="Originating evidence source.",
    )

    evidence_type: EvidenceType = Field(
        description="Specific type of evidence.",
    )

    title: str = Field(
        min_length=1,
        max_length=1000,
        description="Short human-readable evidence title.",
    )

    content: str = Field(
        min_length=1,
        max_length=100000,
        description="Normalized evidence content.",
    )

    timestamp: datetime | None = Field(
        default=None,
        description="Time at which the underlying event occurred.",
    )

    retrieved_at: datetime | None = Field(
        default=None,
        description="Time at which TraceIQ retrieved the evidence.",
    )

    source_ref: EvidenceSourceRef | None = Field(
        default=None,
        description="Reference to the original source.",
    )

    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance to the current investigation.",
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence that this evidence is accurate.",
    )

    confidence_level: ConfidenceLevel | None = Field(
        default=None,
        description="Human-readable evidence confidence.",
    )

    validity: EvidenceValidity = Field(
        default=EvidenceValidity.UNVERIFIED,
        description="Evidence validation state.",
    )

    strength: EvidenceStrength = Field(
        default=EvidenceStrength.MODERATE,
        description="Overall evidence strength.",
    )

    severity: Severity | None = Field(
        default=None,
        description="Severity associated with this evidence.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific structured metadata.",
    )

    content_hash: str | None = Field(
        default=None,
        max_length=128,
        description="Hash used for evidence deduplication/integrity checks.",
    )

    parent_evidence_id: str | None = Field(
        default=None,
        max_length=500,
        description="Parent evidence ID when this evidence is derived from another item.",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Search and classification tags.",
    )


# ============================================================================
# EVIDENCE COLLECTION
# ============================================================================


class EvidenceCollection(BaseTraceIQModel):
    """
    Collection of evidence gathered during an investigation step.
    """

    items: list[Evidence] = Field(
        default_factory=list,
        description="Collected evidence items.",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Total number of evidence items.",
    )

    sources: list[EvidenceSource] = Field(
        default_factory=list,
        description="Distinct evidence providers represented in the collection.",
    )

    collected_at: datetime | None = Field(
        default=None,
        description="Time at which the collection was assembled.",
    )


# ============================================================================
# EVIDENCE RELATIONSHIP
# ============================================================================


class EvidenceRelationshipType(str, Enum):
    """Relationship between two evidence items."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CORROBORATES = "corroborates"
    DERIVED_FROM = "derived_from"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    RELATED_TO = "related_to"


class EvidenceRelationship(BaseTraceIQModel):
    """
    Represents a relationship between two evidence items.

    This allows TraceIQ to build an evidence graph rather than treating
    every retrieved document as an isolated text chunk.
    """

    source_evidence_id: str = Field(
        min_length=1,
        max_length=500,
    )

    target_evidence_id: str = Field(
        min_length=1,
        max_length=500,
    )

    relationship: EvidenceRelationshipType = Field(
        description="Relationship between the evidence items.",
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the relationship.",
    )

    explanation: str | None = Field(
        default=None,
        max_length=10000,
        description="Explanation of why the relationship exists.",
    )


# ============================================================================
# TIMELINE EVENT
# ============================================================================


class TimelineEvent(BaseTraceIQModel):
    """
    Chronological event in an incident timeline.

    A timeline event should be traceable to one or more evidence items.
    """

    id: str = Field(
        min_length=1,
        max_length=500,
        description="Unique timeline event identifier.",
    )

    timestamp: datetime = Field(
        description="Time at which the event occurred.",
    )

    description: str = Field(
        min_length=1,
        max_length=10000,
        description="Description of the event.",
    )

    event_type: EvidenceType | None = Field(
        default=None,
        description="Type of event represented.",
    )

    severity: Severity | None = Field(
        default=None,
        description="Event severity.",
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this event.",
    )

    source: EvidenceSource | None = Field(
        default=None,
        description="Primary source of the event.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence that the timeline event is accurate.",
    )


# ============================================================================
# EVIDENCE VALIDATION RESULT
# ============================================================================


class EvidenceValidationResult(BaseTraceIQModel):
    """
    Result returned by the evidence validation service.

    Validation is deliberately separated from collection so that TraceIQ
    never treats retrieved information as automatically trustworthy.
    """

    evidence_id: str = Field(
        min_length=1,
        max_length=500,
    )

    validity: EvidenceValidity = Field(
        description="Validation result.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the validation result.",
    )

    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons supporting the validation decision.",
    )

    conflicts_with: list[str] = Field(
        default_factory=list,
        description="Evidence IDs that conflict with this item.",
    )

    validated_at: datetime | None = Field(
        default=None,
        description="Time of validation.",
    )


# ============================================================================
# INVESTIGATION EVIDENCE GRAPH
# ============================================================================


class EvidenceGraph(BaseTraceIQModel):
    """
    Graph representation of investigation evidence.

    Nodes are evidence items and edges describe relationships between them.
    """

    nodes: list[Evidence] = Field(
        default_factory=list,
        description="Evidence nodes.",
    )

    relationships: list[EvidenceRelationship] = Field(
        default_factory=list,
        description="Relationships between evidence nodes.",
    )


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "EvidenceSource",
    "EvidenceType",
    "EvidenceValidity",
    "EvidenceStrength",
    "EvidenceSourceRef",
    "Evidence",
    "EvidenceCollection",
    "EvidenceRelationshipType",
    "EvidenceRelationship",
    "TimelineEvent",
    "EvidenceValidationResult",
    "EvidenceGraph",
]