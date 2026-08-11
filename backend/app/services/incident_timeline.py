"""
TraceIQ - Incident Timeline Builder

Constructs a deterministic chronological timeline from unified evidence.

Responsibilities:
- Convert timestamped evidence into timeline events.
- Group evidence occurring at the same timestamp.
- Preserve evidence traceability.
- Sort events chronologically.
- Avoid duplicate evidence references.
- Keep timeline generation deterministic.

This component does not perform:
- LLM reasoning
- Root-cause analysis
- Evidence retrieval
- External API calls
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

import structlog

from app.schemas.evidence import Evidence, TimelineEvent


logger = structlog.get_logger(__name__)


class IncidentTimeline:
    """
    Build a chronological incident timeline from evidence.

    Every timeline event maintains explicit references to the evidence
    that supports it.
    """

    def build(
        self,
        evidence: Iterable[Evidence],
    ) -> list[TimelineEvent]:
        """
        Construct a chronological timeline.

        Evidence without timestamps is intentionally excluded because it
        cannot be placed reliably on a chronological timeline.
        """

        if evidence is None:
            logger.warning(
                "timeline_build_received_none",
            )
            return []

        evidence_items = list(evidence)

        if not evidence_items:
            logger.info(
                "incident_timeline_built",
                evidence_count=0,
                timeline_event_count=0,
            )
            return []

        grouped_events: defaultdict[
            datetime,
            list[Evidence],
        ] = defaultdict(list)

        untimestamped_count = 0

        for item in evidence_items:
            if not isinstance(item, Evidence):
                logger.warning(
                    "timeline_invalid_evidence",
                    evidence_type=type(item).__name__,
                )
                continue

            if item.timestamp is None:
                untimestamped_count += 1
                continue

            grouped_events[item.timestamp].append(item)

        timeline: list[TimelineEvent] = []

        for timestamp, items in grouped_events.items():
            event = self._build_event(
                timestamp=timestamp,
                evidence=items,
            )

            timeline.append(event)

        timeline.sort(
            key=lambda event: event.timestamp,
        )

        logger.info(
            "incident_timeline_built",
            evidence_count=len(evidence_items),
            timestamped_evidence_count=(
                len(evidence_items) - untimestamped_count
            ),
            untimestamped_evidence_count=untimestamped_count,
            timeline_event_count=len(timeline),
        )

        return timeline

    @staticmethod
    def _build_event(
        *,
        timestamp: datetime,
        evidence: list[Evidence],
    ) -> TimelineEvent:
        """
        Create one timeline event from evidence sharing a timestamp.
        """

        ordered_evidence = sorted(
            evidence,
            key=lambda item: (
                item.relevance_score
                if item.relevance_score is not None
                else 0.0,
                item.id,
            ),
            reverse=True,
        )

        evidence_ids: list[str] = []
        descriptions: list[str] = []

        seen_ids: set[str] = set()
        seen_descriptions: set[str] = set()

        for item in ordered_evidence:
            if item.id not in seen_ids:
                evidence_ids.append(item.id)
                seen_ids.add(item.id)

            title = item.title.strip()

            if title and title not in seen_descriptions:
                descriptions.append(title)
                seen_descriptions.add(title)

        description = IncidentTimeline._build_description(
            descriptions,
        )

        return TimelineEvent(
            timestamp=timestamp,
            description=description,
            evidence_ids=evidence_ids,
        )

    @staticmethod
    def _build_description(
        descriptions: list[str],
    ) -> str:
        """
        Build a concise timeline description.

        Multiple evidence records at the same timestamp are represented in
        one event rather than producing multiple visually identical events.
        """

        if not descriptions:
            return "Incident-related event"

        if len(descriptions) == 1:
            return descriptions[0]

        return " | ".join(descriptions)

    @staticmethod
    def sort(
        timeline: Iterable[TimelineEvent],
    ) -> list[TimelineEvent]:
        """
        Sort an existing timeline chronologically.

        This helper is useful when multiple timeline sources are merged.
        """

        events = list(timeline)

        events.sort(
            key=lambda event: event.timestamp,
        )

        return events


__all__ = [
    "IncidentTimeline",
]
