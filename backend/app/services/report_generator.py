"""
TraceIQ - Report Generator

Assembles the final validated InvestigationResponse returned by the API.

Responsibilities:
- Convert validated LLM findings into TraceIQ schemas.
- Build the final evidence-backed investigation report.
- Deduplicate sources.
- Sanitize response fields.
- Preserve evidence traceability.
- Attach processing metadata.

This component does not:
- Call the LLM.
- Collect evidence.
- Perform validation.
- Calculate confidence.
- Generate recommendations.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Mapping, Sequence

import structlog

from app.schemas.evidence import Evidence, TimelineEvent
from app.schemas.investigation import (
    ConfidenceAssessment,
    InvestigationRequest,
    InvestigationResponse,
    LikelyCause,
    Recommendation,
)


logger = structlog.get_logger(__name__)


class ReportGenerator:
    """
    Assemble the final TraceIQ InvestigationResponse.
    """

    def generate(
        self,
        request: InvestigationRequest,
        validated_llm_response: Mapping[str, Any],
        unified_evidence: Sequence[Evidence],
        timeline: Sequence[TimelineEvent],
        confidence: ConfidenceAssessment,
        recommendations: Sequence[Recommendation],
    ) -> InvestigationResponse:
        """
        Generate the final structured investigation report.
        """

        request_id = str(uuid.uuid4())

        evidence = [
            item
            for item in unified_evidence
            if isinstance(item, Evidence)
        ]

        timeline_events = [
            item
            for item in timeline
            if isinstance(item, TimelineEvent)
        ]

        recommendation_items = [
            item
            for item in recommendations
            if isinstance(item, Recommendation)
        ]

        causes = self._build_likely_causes(
            validated_llm_response.get(
                "likely_causes",
                [],
            ),
        )

        follow_up_questions = self._build_follow_up_questions(
            validated_llm_response.get(
                "follow_up_questions",
                [],
            ),
        )

        sources = self._build_sources(
            evidence,
        )

        summary = self._build_summary(
            validated_llm_response.get(
                "summary",
            ),
        )

        processing_metadata = self._build_processing_metadata(
            validated_llm_response,
            evidence,
            timeline_events,
            causes,
            recommendation_items,
        )

        response = InvestigationResponse(
            request_id=request_id,
            incident_id=request.incident_id,
            service=request.service,
            summary=summary,
            timeline=timeline_events,
            evidence=evidence,
            likely_causes=causes,
            confidence=confidence,
            recommendations=recommendation_items,
            follow_up_questions=follow_up_questions,
            sources=sources,
            processing_metadata=processing_metadata,
        )

        logger.info(
            "investigation_report_generated",
            request_id=request_id,
            evidence_count=len(evidence),
            timeline_count=len(timeline_events),
            cause_count=len(causes),
            recommendation_count=len(
                recommendation_items
            ),
            source_count=len(sources),
        )

        return response

    # ========================================================================
    # LIKELY CAUSES
    # ========================================================================

    @staticmethod
    def _build_likely_causes(
        raw_causes: Any,
    ) -> list[LikelyCause]:
        """
        Convert validated cause dictionaries into schema objects.

        The EvidenceValidator is responsible for validating evidence IDs.
        This layer only performs final schema-safe conversion.
        """

        if not isinstance(
            raw_causes,
            Sequence,
        ) or isinstance(
            raw_causes,
            (str, bytes),
        ):
            return []

        causes: list[LikelyCause] = []

        for raw_cause in raw_causes:
            if not isinstance(
                raw_cause,
                Mapping,
            ):
                continue

            try:
                cause = LikelyCause(
                    cause=str(
                        raw_cause.get(
                            "cause",
                            "",
                        )
                    ).strip(),
                    explanation=str(
                        raw_cause.get(
                            "explanation",
                            "",
                        )
                    ).strip(),
                    supporting_evidence_ids=(
                        ReportGenerator._normalize_ids(
                            raw_cause.get(
                                "supporting_evidence_ids",
                                [],
                            )
                        )
                    ),
                    confidence=(
                        ReportGenerator._normalize_confidence(
                            raw_cause.get(
                                "confidence",
                                "low",
                            )
                        )
                    ),
                )

            except Exception:
                logger.warning(
                    "invalid_likely_cause_skipped",
                    cause=raw_cause.get("cause"),
                    exc_info=True,
                )
                continue

            if not cause.cause:
                continue

            if not cause.explanation:
                continue

            causes.append(cause)

        return causes

    # ========================================================================
    # FOLLOW-UP QUESTIONS
    # ========================================================================

    @staticmethod
    def _build_follow_up_questions(
        questions: Any,
    ) -> list[str]:
        """
        Build a clean list of follow-up questions.
        """

        if not isinstance(
            questions,
            Sequence,
        ) or isinstance(
            questions,
            (str, bytes),
        ):
            return []

        result: list[str] = []

        seen: set[str] = set()

        for question in questions:
            text = str(
                question,
            ).strip()

            if not text:
                continue

            if len(text) > 500:
                text = (
                    text[:500].rstrip()
                    + "..."
                )

            normalized = text.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(text)

            if len(result) >= 10:
                break

        return result

    # ========================================================================
    # SOURCES
    # ========================================================================

    @staticmethod
    def _build_sources(
        evidence: Sequence[Evidence],
    ) -> list[str]:
        """
        Return distinct evidence sources in deterministic order.
        """

        sources: set[str] = set()

        for item in evidence:
            source = item.source.strip()

            if source:
                sources.add(source)

        return sorted(
            sources,
            key=str.casefold,
        )

    # ========================================================================
    # SUMMARY
    # ========================================================================

    @staticmethod
    def _build_summary(
        summary: Any,
    ) -> str:
        """
        Normalize the final investigation summary.
        """

        if summary is None:
            return (
                "No investigation summary was generated."
            )

        text = str(
            summary,
        ).strip()

        if not text:
            return (
                "No investigation summary was generated."
            )

        if len(text) > 12_000:
            text = (
                text[:12_000].rstrip()
                + "..."
            )

        return text

    # ========================================================================
    # PROCESSING METADATA
    # ========================================================================

    @staticmethod
    def _build_processing_metadata(
        validated_response: Mapping[str, Any],
        evidence: Sequence[Evidence],
        timeline: Sequence[TimelineEvent],
        causes: Sequence[LikelyCause],
        recommendations: Sequence[Recommendation],
    ) -> dict[str, Any]:
        """
        Build safe metadata describing report construction.

        Internal validation metadata is not copied wholesale into the public
        response.
        """

        validation = validated_response.get(
            "_validation",
            {},
        )

        metadata: dict[str, Any] = {
            "llm_used": True,
            "evidence_count": len(evidence),
            "timeline_event_count": len(timeline),
            "likely_cause_count": len(causes),
            "recommendation_count": len(
                recommendations
            ),
            "grounded": (
                bool(
                    validation.get(
                        "grounded",
                        False,
                    )
                )
                if isinstance(
                    validation,
                    Mapping,
                )
                else False
            ),
        }

        return metadata

    # ========================================================================
    # NORMALIZATION HELPERS
    # ========================================================================

    @staticmethod
    def _normalize_ids(
        values: Any,
    ) -> list[str]:
        """
        Normalize and deduplicate identifier values.
        """

        if not isinstance(
            values,
            Sequence,
        ) or isinstance(
            values,
            (str, bytes),
        ):
            return []

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            if value is None:
                continue

            identifier = str(
                value,
            ).strip()

            if not identifier:
                continue

            if identifier in seen:
                continue

            seen.add(identifier)
            result.append(identifier)

        return result

    @staticmethod
    def _normalize_confidence(
        value: Any,
    ):
        """
        Normalize confidence values before schema construction.
        """

        normalized = (
            str(value).strip().lower()
            if value is not None
            else "low"
        )

        aliases = {
            "very high": "high",
            "certain": "high",
            "strong": "high",
            "moderate": "medium",
            "medium-high": "medium",
            "medium high": "medium",
        }

        normalized = aliases.get(
            normalized,
            normalized,
        )

        if normalized not in {
            "low",
            "medium",
            "high",
        }:
            normalized = "low"

        return normalized


__all__ = [
    "ReportGenerator",
]