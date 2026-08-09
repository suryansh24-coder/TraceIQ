from typing import List, Dict, Any
from app.schemas.investigation import Recommendation
from app.schemas.common import Severity

class RecommendationEngine:
    """
    Filters and formats recommendations.
    """
    def generate(self, validated_response: Dict[str, Any]) -> List[Recommendation]:
        recs_data = validated_response.get("recommendations", [])
        
        recommendations = []
        for r in recs_data:
            priority = r.get("priority", "medium").lower()
            if priority not in [s.value for s in Severity]:
                priority = "medium"
                
            recommendations.append(Recommendation(
                action=r.get("action", ""),
                reason=r.get("reason", ""),
                priority=Severity(priority),
                supporting_evidence_ids=r.get("supporting_evidence_ids", [])
            ))
            
        # Prioritize HIGH > MEDIUM > LOW
        priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_map.get(x.priority.value, 4))
        
        return recommendations
