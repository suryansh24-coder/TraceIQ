from typing import List
from app.schemas.evidence import Evidence
import structlog

logger = structlog.get_logger()

class EvidenceBuilder:
    """
    Normalizes, deduplicates, and structures evidence from various sources.
    """
    def build(self, raw_evidence_list: List[Evidence]) -> List[Evidence]:
        """
        Merge and sort evidence, removing exact duplicates based on ID.
        """
        seen_ids = set()
        unified = []
        
        for item in raw_evidence_list:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unified.append(item)
            else:
                logger.debug("duplicate_evidence_ignored", id=item.id)
                
        # Sort by relevance if available, otherwise by timestamp
        unified.sort(
            key=lambda x: (
                x.relevance_score if x.relevance_score is not None else 0.0,
                x.timestamp.timestamp() if x.timestamp else 0.0
            ),
            reverse=True
        )
        
        logger.info("evidence_unified", total_items=len(unified))
        return unified
