from typing import List, Dict, Any
from app.schemas.evidence import Evidence
from app.schemas.common import ConfidenceLevel
from app.schemas.investigation import ConfidenceAssessment

class ConfidenceCalculator:
    """
    Calculates a heuristic confidence score for an investigation.
    """
    def calculate(self, validated_response: Dict[str, Any], evidence: List[Evidence]) -> ConfidenceAssessment:
        basis = []
        score = 0.0
        
        # Factor 1: Evidence Volume
        if len(evidence) >= 5:
            score += 0.3
            basis.append("Multiple pieces of evidence available")
        elif len(evidence) > 0:
            score += 0.1
            basis.append("Some evidence available")
            
        # Factor 2: Source Diversity
        sources = {e.source for e in evidence}
        if len(sources) >= 3:
            score += 0.3
            basis.append("Evidence corroborated across multiple independent sources")
        elif len(sources) == 2:
            score += 0.2
            basis.append("Evidence corroborated across two sources")
            
        # Factor 3: Historical Match (Qdrant)
        if any(e.source == "qdrant" or e.evidence_type == "historical_incident" for e in evidence):
            score += 0.2
            basis.append("Matching historical incident found")
            
        # Factor 4: LLM Confidence
        causes = validated_response.get("likely_causes", [])
        if causes:
            llm_conf = causes[0].get("confidence", "low")
            if llm_conf == "high":
                score += 0.2
                basis.append("Strong analytical alignment")
            elif llm_conf == "medium":
                score += 0.1
                basis.append("Moderate analytical alignment")
        else:
            basis.append("No valid root causes identified")
            score = max(0.0, score - 0.4) # Penalize heavily if no cause found
            
        # Cap score
        score = min(1.0, max(0.0, score))
        
        if score >= 0.8:
            level = ConfidenceLevel.HIGH
        elif score >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
            
        return ConfidenceAssessment(
            level=level,
            score=score,
            basis=basis
        )
