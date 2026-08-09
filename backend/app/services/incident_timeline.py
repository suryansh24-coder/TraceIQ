from typing import List
from app.schemas.evidence import Evidence, TimelineEvent
from app.utils.timestamps import sort_events_chronologically

class IncidentTimeline:
    """
    Constructs a chronological timeline from a set of evidence.
    """
    def build(self, evidence: List[Evidence]) -> List[TimelineEvent]:
        timeline_events = []
        for e in evidence:
            if e.timestamp:
                timeline_events.append(TimelineEvent(
                    timestamp=e.timestamp,
                    description=e.title,
                    evidence_ids=[e.id]
                ))
        
        # Sort chronologically
        events_dicts = [t.model_dump() for t in timeline_events]
        sorted_dicts = sort_events_chronologically(events_dicts)
        
        return [TimelineEvent(**d) for d in sorted_dicts]
