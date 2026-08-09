from typing import List, Dict, Any, Optional
from pydantic import Field
from app.schemas.common import BaseTraceIQModel, Severity, ConfidenceLevel
from app.schemas.evidence import Evidence, TimelineEvent

class InvestigationRequest(BaseTraceIQModel):
    query: str = Field(..., description="The engineer's natural language request")
    incident_id: Optional[str] = Field(None, description="ID of the related incident if known")
    service: Optional[str] = Field(None, description="The service involved")
    severity: Optional[Severity] = Field(None, description="Severity of the incident")
    conversation_id: Optional[str] = Field(None, description="ID for conversation continuity")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class LikelyCause(BaseTraceIQModel):
    cause: str = Field(..., description="The hypothesized root cause")
    explanation: str = Field(..., description="Detailed explanation of the cause")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence supporting this cause")
    confidence: ConfidenceLevel = Field(..., description="Confidence level for this cause")

class Recommendation(BaseTraceIQModel):
    action: str = Field(..., description="The recommended action to take")
    reason: str = Field(..., description="Why this action is recommended")
    priority: Severity = Field(..., description="Priority of the recommendation")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence supporting this recommendation")

class ConfidenceAssessment(BaseTraceIQModel):
    level: ConfidenceLevel = Field(..., description="Overall confidence level")
    score: float = Field(..., description="Heuristic score (0.0 to 1.0)")
    basis: List[str] = Field(default_factory=list, description="Reasons for this confidence assessment")

class InvestigationResponse(BaseTraceIQModel):
    request_id: str = Field(..., description="Unique ID for this investigation request")
    incident_id: Optional[str] = Field(None, description="ID of the related incident")
    service: Optional[str] = Field(None, description="The service involved")
    summary: str = Field(..., description="High-level summary of the investigation")
    timeline: List[TimelineEvent] = Field(default_factory=list, description="Chronological timeline of events")
    evidence: List[Evidence] = Field(default_factory=list, description="List of all collected evidence")
    likely_causes: List[LikelyCause] = Field(default_factory=list, description="Hypothesized root causes")
    confidence: ConfidenceAssessment = Field(..., description="Confidence assessment for the investigation")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Actionable recommendations")
    follow_up_questions: List[str] = Field(default_factory=list, description="Questions the engineer might ask next")
    sources: List[str] = Field(default_factory=list, description="List of distinct sources used")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the investigation process")
