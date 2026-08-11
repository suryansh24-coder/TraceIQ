"""
TraceIQ - Evidence Builder

Normalizes, deduplicates, validates, ranks, and bounds evidence collected
from different engineering systems.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from typing import Iterable

import structlog

from app.config import settings
from app.schemas.evidence import Evidence


logger = structlog.get_logger(__name__)


DEFAULT_MAX_EVIDENCE = 250

MIN_RELEVANCE_SCORE = 0.0
MAX_RELEVANCE_SCORE = 1.0


class EvidenceBuilder:
    """
    Build a unified, deterministic evidence collection.

    Processing stages:

        1. Filter invalid evidence
        2. Normalize fields
        3. Deduplicate evidence
        4. Merge complementary duplicates
        5. Calculate deterministic ranking
        6. Sort evidence
        7. Apply a bounded output size
    """

    def __init__(
        self,
        *,
        max_evidence: int | None = None,
    ) -> None:
        configured_limit = (
            max_evidence
            if max_evidence is not None
            else getattr(
                settings,
                "evidence_max_items",
                DEFAULT_MAX_EVIDENCE,
            )
        )

        self.max_evidence = max(
            1,
            int(configured_limit),
        )

    def build(
        self,
        raw_evidence_list: Iterable[Evidence],
    ) -> list[Evidence]:
        """
        Normalize and unify evidence.

        Args:
            raw_evidence_list:
                Evidence returned by integrations, RAG, demo data, etc.

        Returns:
            Deterministically ordered and bounded evidence list.
        """

        if raw_evidence_list is None:
            logger.warning(
                "evidence_builder_received_none",
            )
            return []

        raw_items = list(raw_evidence_list)

        if not raw_items:
            logger.info(
                "evidence_unified",
                input_items=0,
                output_items=0,
                duplicates_removed=0,
            )
            return []

        normalized: list[Evidence] = []

        invalid_count = 0

        for item in raw_items:
            normalized_item = self._normalize_evidence(item)

            if normalized_item is None:
                invalid_count += 1
                continue

            normalized.append(normalized_item)

        unified = self._deduplicate_and_merge(
            normalized,
        )

        duplicates_removed = (
            len(normalized) - len(unified)
        )

        ranked = self._rank_evidence(
            unified,
        )

        bounded = ranked[: self.max_evidence]

        truncated_count = max(
            0,
            len(ranked) - len(bounded),
        )

        logger.info(
            "evidence_unified",
            input_items=len(raw_items),
            normalized_items=len(normalized),
            invalid_items=invalid_count,
            duplicates_removed=duplicates_removed,
            total_items=len(bounded),
            truncated_items=truncated_count,
        )

        return bounded

    @staticmethod
    def _normalize_evidence(
        item: Evidence,
    ) -> Evidence | None:
        """
        Normalize an Evidence object without mutating the original.
        """

        if not isinstance(item, Evidence):
            logger.warning(
                "invalid_evidence_type",
                evidence_type=type(item).__name__,
            )
            return None

        evidence_id = (
            str(item.id).strip()
            if item.id is not None
            else ""
        )

        if not evidence_id:
            logger.warning(
                "evidence_missing_id",
            )
            return None

        source = (
            str(item.source).strip()
            if item.source is not None
            else "unknown"
        )

        title = (
            str(item.title).strip()
            if item.title is not None
            else "Untitled evidence"
        )

        content = (
            str(item.content).strip()
            if item.content is not None
            else ""
        )

        evidence_type = (
            str(item.evidence_type).strip()
            if item.evidence_type is not None
            else "unknown"
        )

        if not content:
            logger.debug(
                "evidence_empty_content",
                evidence_id=evidence_id,
            )

        relevance_score = (
            EvidenceBuilder._normalize_score(
                item.relevance_score,
            )
        )

        metadata = dict(item.metadata or {})

        return item.model_copy(
            update={
                "id": evidence_id,
                "source": source,
                "title": title,
                "content": content,
                "evidence_type": evidence_type,
                "relevance_score": relevance_score,
                "metadata": metadata,
            },
        )

    def _deduplicate_and_merge(
        self,
        evidence_items: list[Evidence],
    ) -> list[Evidence]:
        """
        Deduplicate evidence by ID.

        Complementary duplicate records are merged rather than discarded.
        """

        merged: OrderedDict[str, Evidence] = OrderedDict()

        for item in evidence_items:
            existing = merged.get(item.id)

            if existing is None:
                merged[item.id] = item
                continue

            merged[item.id] = self._merge_evidence(
                existing,
                item,
            )

            logger.debug(
                "duplicate_evidence_merged",
                evidence_id=item.id,
            )

        return list(merged.values())

    @staticmethod
    def _merge_evidence(
        primary: Evidence,
        secondary: Evidence,
    ) -> Evidence:
        """
        Merge two Evidence objects with the same ID.
        """

        title = EvidenceBuilder._choose_richer_text(
            primary.title,
            secondary.title,
        )

        content = EvidenceBuilder._choose_richer_text(
            primary.content,
            secondary.content,
        )

        timestamp = (
            primary.timestamp
            or secondary.timestamp
        )

        relevance_score = EvidenceBuilder._max_score(
            primary.relevance_score,
            secondary.relevance_score,
        )

        evidence_type = EvidenceBuilder._choose_richer_text(
            primary.evidence_type,
            secondary.evidence_type,
        )

        source = EvidenceBuilder._merge_sources(
            primary.source,
            secondary.source,
        )

        metadata = dict(primary.metadata or {})

        secondary_metadata = dict(
            secondary.metadata or {},
        )

        for key, value in secondary_metadata.items():
            if key not in metadata:
                metadata[key] = value
            elif metadata[key] != value:
                metadata[f"{key}_secondary"] = value

        return primary.model_copy(
            update={
                "source": source,
                "title": title,
                "content": content,
                "timestamp": timestamp,
                "relevance_score": relevance_score,
                "evidence_type": evidence_type,
                "metadata": metadata,
            },
        )

    def _rank_evidence(
        self,
        evidence_items: list[Evidence],
    ) -> list[Evidence]:
        """
        Rank evidence using deterministic signals.

        Ranking priority:

            1. Explicit relevance score
            2. Evidence completeness
            3. Timestamp recency
        """

        now = datetime.now().astimezone()

        scored_items: list[
            tuple[float, Evidence]
        ] = []

        for item in evidence_items:
            score = self._calculate_rank_score(
                item,
                now,
            )

            scored_items.append(
                (
                    score,
                    item,
                )
            )

        scored_items.sort(
            key=lambda pair: (
                pair[0],
                self._timestamp_value(pair[1]),
                pair[1].id,
            ),
            reverse=True,
        )

        return [
            item
            for _, item in scored_items
        ]

    @classmethod
    def _calculate_rank_score(
        cls,
        item: Evidence,
        now: datetime,
    ) -> float:
        """
        Calculate deterministic ranking score.
        """

        relevance = (
            item.relevance_score
            if item.relevance_score is not None
            else 0.0
        )

        relevance_component = relevance * 0.70

        completeness = cls._completeness_score(
            item,
        )

        completeness_component = completeness * 0.15

        recency = cls._recency_score(
            item.timestamp,
            now,
        )

        recency_component = recency * 0.15

        return (
            relevance_component
            + completeness_component
            + recency_component
        )

    @staticmethod
    def _completeness_score(
        item: Evidence,
    ) -> float:
        """Estimate whether the evidence contains useful fields."""

        score = 0.0

        if item.title.strip():
            score += 0.25

        if item.content.strip():
            score += 0.35

        if item.source.strip():
            score += 0.15

        if item.evidence_type.strip():
            score += 0.15

        if item.timestamp is not None:
            score += 0.10

        return min(
            score,
            1.0,
        )

    @staticmethod
    def _recency_score(
        timestamp: datetime | None,
        now: datetime,
    ) -> float:
        """
        Convert timestamp recency into a 0..1 score.
        """

        if timestamp is None:
            return 0.0

        try:
            event_time = timestamp

            if event_time.tzinfo is None:
                event_time = event_time.replace(
                    tzinfo=now.tzinfo,
                )

            age_seconds = max(
                0.0,
                (
                    now - event_time
                ).total_seconds(),
            )

        except (TypeError, ValueError):
            return 0.0

        decay_window = 7 * 24 * 60 * 60

        return max(
            0.0,
            1.0 - (
                age_seconds / decay_window
            ),
        )

    @staticmethod
    def _normalize_score(
        score: float | None,
    ) -> float | None:
        """Clamp relevance scores to the valid 0..1 range."""

        if score is None:
            return None

        try:
            value = float(score)
        except (TypeError, ValueError):
            return None

        return max(
            MIN_RELEVANCE_SCORE,
            min(
                value,
                MAX_RELEVANCE_SCORE,
            ),
        )

    @staticmethod
    def _max_score(
        first: float | None,
        second: float | None,
    ) -> float | None:
        """Return the strongest available relevance score."""

        if first is None:
            return second

        if second is None:
            return first

        return max(
            first,
            second,
        )

    @staticmethod
    def _choose_richer_text(
        first: str,
        second: str,
    ) -> str:
        """
        Choose the richer textual representation.
        """

        first_clean = (
            first.strip()
            if first
            else ""
        )

        second_clean = (
            second.strip()
            if second
            else ""
        )

        if not first_clean:
            return second_clean

        if not second_clean:
            return first_clean

        return (
            second_clean
            if len(second_clean) > len(first_clean)
            else first_clean
        )

    @staticmethod
    def _merge_sources(
        first: str,
        second: str,
    ) -> str:
        """
        Merge source identifiers without unnecessary duplication.
        """

        first_sources = {
            value.strip()
            for value in first.split(",")
            if value.strip()
        }

        second_sources = {
            value.strip()
            for value in second.split(",")
            if value.strip()
        }

        combined = first_sources | second_sources

        return ", ".join(
            sorted(combined),
        )

    @staticmethod
    def _timestamp_value(
        item: Evidence,
    ) -> float:
        """Return a safe timestamp value for deterministic sorting."""

        if item.timestamp is None:
            return 0.0

        try:
            return item.timestamp.timestamp()
        except (ValueError, OSError):
            return 0.0


__all__ = [
    "EvidenceBuilder",
]