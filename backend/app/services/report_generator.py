from typing import Dict, Any, List
import uuid
from app.schemas.investigation import (
    InvestigationRequest, 
    InvestigationResponse, 
    LikelyCause
)
from app.schemas.evidence import Evidence, TimelineEvent
from app.schemas.investigation import ConfidenceAssessment, Recommendation

class ReportGenerator:
    """
    Assembles the final structured InvestigationResponse.
    """
    def generate(
        self,
        request: InvestigationRequest,
        validated_llm_response: Dict[str, Any],
        unified_evidence: List[Evidence],
        timeline: List[TimelineEvent],
        confidence: ConfidenceAssessment,
        recommendations: List[Recommendation]
    ) -> InvestigationResponse:
        
        sources = list({e.source for e in unified_evidence})
        
        causes = [
            LikelyCause(**c) for c in validated_llm_response.get("likely_causes", [])
        ]
        
        return InvestigationResponse(
            request_id=str(uuid.uuid4()),
            incident_id=request.incident_id,
            service=request.service,
            summary=validated_llm_response.get("summary", ""),
            timeline=timeline,
            evidence=unified_evidence,
            likely_causes=causes,
            confidence=confidence,
            recommendations=recommendations,
            follow_up_questions=validated_llm_response.get("follow_up_questions", []),
            sources=sources,
            processing_metadata={"llm_used": True}
        )
