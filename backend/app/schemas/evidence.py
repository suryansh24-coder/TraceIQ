from typing import List, Dict, Any, Optional
from pydantic import Field
from datetime import datetime
from app.schemas.common import BaseTraceIQModel, Severity, ConfidenceLevel

class Evidence(BaseTraceIQModel):
    id: str = Field(..., description="Unique identifier for the evidence")
    source: str = Field(..., description="Source of the evidence (e.g., github, monitoring, qdrant)")
    title: str = Field(..., description="Short title describing the evidence")
    content: str = Field(..., description="The actual evidence text or data")
    timestamp: Optional[datetime] = Field(None, description="When the event occurred")
    relevance_score: Optional[float] = Field(None, description="Score indicating relevance to the investigation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or raw data")
    evidence_type: str = Field(..., description="Type of evidence (e.g., commit, alert, log, runbook)")

class TimelineEvent(BaseTraceIQModel):
    timestamp: datetime = Field(..., description="When the event occurred")
    description: str = Field(..., description="Description of the event")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence supporting this event")
