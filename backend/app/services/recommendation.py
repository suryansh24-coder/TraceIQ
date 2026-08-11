"""
TraceIQ - Recommendation Engine

Converts validated LLM recommendations into strongly typed TraceIQ
Recommendation objects.

Responsibilities:
- Validate recommendation structure.
- Normalize priority/severity.
- Remove malformed recommendations.
- Remove duplicates.
- Preserve evidence references.
- Rank recommendations by operational priority.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import structlog

from app.schemas.common import Severity
from app.schemas.investigation import Recommendation


logger = structlog.get_logger(__name__)


class RecommendationEngine:
    """
    Generate deterministic, validated recommendations from an already
    evidence-validated LLM response.
    """

    _PRIORITY_ORDER = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }

    _MAX_RECOMMENDATIONS = 10

    def generate(
        self,
        validated_response: Mapping[str, Any] | None,
    ) -> list[Recommendation]:
        """
        Convert validated recommendation dictionaries into Recommendation
        schema objects.

        Invalid recommendations are skipped rather than causing the complete
        investigation to fail.
        """

        if not isinstance(validated_response, Mapping):
            logger.warning(
                "recommendation_input_invalid",
            )
            return []

        recommendations_data = validated_response.get(
            "recommendations",
            [],
        )

        if not isinstance(
            recommendations_data,
            Sequence,
        ) or isinstance(
            recommendations_data,
            (str, bytes),
        ):
            logger.warning(
                "recommendations_not_a_sequence",
            )
            return []

        recommendations: list[Recommendation] = []

        seen: set[tuple[str, tuple[str, ...]]] = set()

        for index, raw_recommendation in enumerate(
            recommendations_data,
        ):
            if not isinstance(
                raw_recommendation,
                Mapping,
            ):
                logger.warning(
                    "invalid_recommendation",
                    index=index,
                )
                continue

            action = self._clean_text(
                raw_recommendation.get("action"),
            )

            reason = self._clean_text(
                raw_recommendation.get("reason"),
            )

            if not action:
                logger.warning(
                    "recommendation_action_missing",
                    index=index,
                )
                continue

            if not reason:
                logger.warning(
                    "recommendation_reason_missing",
                    action=action,
                )
                continue

            priority = self._normalize_priority(
                raw_recommendation.get("priority"),
            )

            evidence_ids = self._normalize_evidence_ids(
                raw_recommendation.get(
                    "supporting_evidence_ids",
                    [],
                ),
            )

            deduplication_key = (
                action.lower(),
                tuple(evidence_ids),
            )

            if deduplication_key in seen:
                logger.debug(
                    "duplicate_recommendation_removed",
                    action=action,
                )
                continue

            seen.add(
                deduplication_key,
            )

            recommendations.append(
                Recommendation(
                    action=action,
                    reason=reason,
                    priority=priority,
                    supporting_evidence_ids=evidence_ids,
                )
            )

            if len(recommendations) >= self._MAX_RECOMMENDATIONS:
                break

        recommendations.sort(
            key=lambda recommendation: (
                self._PRIORITY_ORDER.get(
                    recommendation.priority,
                    99,
                ),
                recommendation.action.lower(),
            ),
        )

        logger.info(
            "recommendations_generated",
            count=len(recommendations),
        )

        return recommendations

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        """
        Normalize recommendation text.
        """

        if value is None:
            return ""

        text = str(value).strip()

        if len(text) > 4_000:
            text = text[:4_000].rstrip() + "..."

        return text

    @staticmethod
    def _normalize_priority(
        priority: Any,
    ) -> Severity:
        """
        Normalize arbitrary model priority values to TraceIQ Severity.
        """

        if isinstance(
            priority,
            Severity,
        ):
            return priority

        value = (
            str(priority).strip().lower()
            if priority is not None
            else "medium"
        )

        direct_mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
        }

        if value in direct_mapping:
            return direct_mapping[value]

        aliases = {
            "urgent": Severity.CRITICAL,
            "immediate": Severity.CRITICAL,
            "emergency": Severity.CRITICAL,
            "p0": Severity.CRITICAL,
            "p1": Severity.HIGH,
            "important": Severity.HIGH,
            "p2": Severity.MEDIUM,
            "normal": Severity.MEDIUM,
            "p3": Severity.LOW,
            "minor": Severity.LOW,
        }

        return aliases.get(
            value,
            Severity.MEDIUM,
        )

    @staticmethod
    def _normalize_evidence_ids(
        evidence_ids: Any,
    ) -> list[str]:
        """
        Normalize and deduplicate evidence IDs while preserving order.
        """

        if not isinstance(
            evidence_ids,
            Sequence,
        ) or isinstance(
            evidence_ids,
            (str, bytes),
        ):
            return []

        normalized: list[str] = []
        seen: set[str] = set()

        for evidence_id in evidence_ids:
            if evidence_id is None:
                continue

            value = str(
                evidence_id,
            ).strip()

            if not value or value in seen:
                continue

            seen.add(value)
            normalized.append(value)

        return normalized


__all__ = [
    "RecommendationEngine",
]