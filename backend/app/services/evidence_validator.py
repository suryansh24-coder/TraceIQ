from typing import Dict, Any, List
from app.schemas.evidence import Evidence
import structlog

logger = structlog.get_logger()

class EvidenceValidator:
    """
    Validates LLM-generated responses against provided evidence.
    Major anti-hallucination feature.
    """
    def validate(self, llm_response: Dict[str, Any], provided_evidence: List[Evidence]) -> Dict[str, Any]:
        valid_ids = {e.id for e in provided_evidence}
        
        # Validate likely causes
        valid_causes = []
        for cause in llm_response.get("likely_causes", []):
            cause_ev_ids = cause.get("supporting_evidence_ids", [])
            # Check if any ID is hallucinated
            if any(eid not in valid_ids for eid in cause_ev_ids):
                logger.warning("hallucinated_evidence_id_in_cause", cause=cause.get("cause"), ids=cause_ev_ids)
                continue
                
            if not cause_ev_ids:
                logger.warning("cause_missing_evidence_ids", cause=cause.get("cause"))
                continue
                
            valid_causes.append(cause)
            
        llm_response["likely_causes"] = valid_causes
        
        # Validate recommendations
        valid_recs = []
        for rec in llm_response.get("recommendations", []):
            rec_ev_ids = rec.get("supporting_evidence_ids", [])
            if any(eid not in valid_ids for eid in rec_ev_ids):
                logger.warning("hallucinated_evidence_id_in_recommendation", action=rec.get("action"))
                continue
            valid_recs.append(rec)
            
        llm_response["recommendations"] = valid_recs
        
        # Check if the overall response is basically unsupported
        if not valid_causes and not valid_recs:
            logger.warning("llm_response_invalidated")
            llm_response["summary"] = "Insufficient evidence to determine a reliable root cause."
            
        return llm_response
