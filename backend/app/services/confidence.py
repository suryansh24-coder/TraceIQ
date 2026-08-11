"""
TraceIQ - Confidence Calculator

Calculates a deterministic confidence assessment for an investigation based
on evidence quality, source diversity, historical correlation, and validated
LLM reasoning.

The calculator does not call external services and never invents evidence.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.schemas.common import ConfidenceLevel
from app.schemas.evidence import Evidence
from app.schemas.investigation import ConfidenceAssessment


class ConfidenceCalculator:
    """
    Calculates an evidence-grounded confidence score.

    Factors:
        - Evidence volume
        - Source diversity
        - Historical evidence
        - LLM analytical confidence
        - Evidence grounding/validation
    """

    def calculate(
        self,
        validated_response: Mapping[str, Any],
        evidence: Sequence[Evidence],
    ) -> ConfidenceAssessment:
        """
        Calculate the overall investigation confidence.

        Returns:
            ConfidenceAssessment with normalized score, level, and basis.
        """

        if not isinstance(validated_response, Mapping):
            validated_response = {}

        evidence_items = [
            item
            for item in evidence
            if isinstance(item, Evidence)
        ]

        basis: list[str] = []
        score = 0.0

        # ====================================================================
        # FACTOR 1 — EVIDENCE VOLUME
        # ====================================================================

        evidence_count = len(evidence_items)

        if evidence_count >= 10:
            score += 0.25
            basis.append(
                "Strong volume of supporting evidence available"
            )

        elif evidence_count >= 5:
            score += 0.20
            basis.append(
                "Multiple pieces of supporting evidence available"
            )

        elif evidence_count >= 2:
            score += 0.10
            basis.append(
                "Multiple evidence items available"
            )

        elif evidence_count == 1:
            score += 0.05
            basis.append(
                "Only one evidence item available"
            )

        else:
            basis.append(
                "No evidence available"
            )

        # ====================================================================
        # FACTOR 2 — SOURCE DIVERSITY
        # ====================================================================

        sources = {
            item.source.strip().lower()
            for item in evidence_items
            if item.source and item.source.strip()
        }

        source_count = len(sources)

        if source_count >= 4:
            score += 0.25
            basis.append(
                "Evidence corroborated across multiple independent sources"
            )

        elif source_count == 3:
            score += 0.20
            basis.append(
                "Evidence corroborated across three sources"
            )

        elif source_count == 2:
            score += 0.15
            basis.append(
                "Evidence corroborated across two sources"
            )

        elif source_count == 1:
            score += 0.05
            basis.append(
                "Evidence comes from a single source"
            )

        else:
            basis.append(
                "Evidence source information is unavailable"
            )

        # ====================================================================
        # FACTOR 3 — HISTORICAL CORRELATION
        # ====================================================================

        historical_evidence = [
            item
            for item in evidence_items
            if (
                item.source.strip().lower() == "qdrant"
                or item.evidence_type.strip().lower()
                in {
                    "historical_incident",
                    "historical",
                    "incident_history",
                }
            )
        ]

        if historical_evidence:
            score += 0.15
            basis.append(
                "Relevant historical incident evidence is available"
            )

        else:
            basis.append(
                "No historical incident match was identified"
            )

        # ====================================================================
        # FACTOR 4 — VALIDATED ROOT-CAUSE ANALYSIS
        # ====================================================================

        causes = validated_response.get(
            "likely_causes",
            [],
        )

        if not isinstance(causes, list):
            causes = []

        valid_causes = [
            cause
            for cause in causes
            if isinstance(cause, Mapping)
        ]

        if valid_causes:
            best_llm_confidence = self._best_cause_confidence(
                valid_causes,
            )

            if best_llm_confidence == "high":
                score += 0.20
                basis.append(
                    "Strong analytical alignment with the available evidence"
                )

            elif best_llm_confidence == "medium":
                score += 0.12
                basis.append(
                    "Moderate analytical alignment with the available evidence"
                )

            else:
                score += 0.05
                basis.append(
                    "A possible root cause was identified with low confidence"
                )

        else:
            score -= 0.25
            basis.append(
                "No validated root cause was identified"
            )

        # ====================================================================
        # FACTOR 5 — VALIDATION / GROUNDING
        # ====================================================================

        validation = validated_response.get(
            "_validation",
            {},
        )

        if isinstance(validation, Mapping):
            grounded = bool(
                validation.get(
                    "grounded",
                    False,
                )
            )

            validation_successful = bool(
                validation.get(
                    "validated",
                    False,
                )
            )

            if grounded and validation_successful:
                score += 0.15
                basis.append(
                    "LLM findings passed evidence-grounding validation"
                )

            elif validation_successful:
                score += 0.05
                basis.append(
                    "LLM response passed structural validation"
                )

            else:
                score -= 0.15
                basis.append(
                    "LLM response did not pass evidence-grounding validation"
                )

        # ====================================================================
        # FACTOR 6 — SUPPORTING EVIDENCE COVERAGE
        # ====================================================================

        evidence_ids = {
            item.id
            for item in evidence_items
        }

        supported_cause_count = 0

        for cause in valid_causes:
            supporting_ids = cause.get(
                "supporting_evidence_ids",
                [],
            )

            if not isinstance(
                supporting_ids,
                list,
            ):
                continue

            if any(
                evidence_id in evidence_ids
                for evidence_id in supporting_ids
            ):
                supported_cause_count += 1

        if valid_causes:
            coverage = (
                supported_cause_count
                / len(valid_causes)
            )

            if coverage >= 0.75:
                score += 0.10
                basis.append(
                    "Most identified causes have direct evidence support"
                )

            elif coverage > 0:
                score += 0.05
                basis.append(
                    "Some identified causes have direct evidence support"
                )

            else:
                score -= 0.10
                basis.append(
                    "Identified causes lack direct evidence coverage"
                )

        # ====================================================================
        # NORMALIZE SCORE
        # ====================================================================

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        # ====================================================================
        # CONFIDENCE LEVEL
        # ====================================================================

        if score >= 0.80:
            level = ConfidenceLevel.HIGH

        elif score >= 0.50:
            level = ConfidenceLevel.MEDIUM

        else:
            level = ConfidenceLevel.LOW

        return ConfidenceAssessment(
            level=level,
            score=round(
                score,
                3,
            ),
            basis=basis,
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _best_cause_confidence(
        causes: Sequence[Mapping[str, Any]],
    ) -> str:
        """
        Return the strongest confidence among validated causes.
        """

        confidence_rank = {
            "low": 1,
            "medium": 2,
            "high": 3,
        }

        best = "low"
        best_rank = 0

        for cause in causes:
            value = str(
                cause.get(
                    "confidence",
                    "low",
                )
            ).strip().lower()

            if value in {
                "very high",
                "certain",
                "strong",
            }:
                value = "high"

            elif value in {
                "moderate",
                "medium-high",
                "medium high",
            }:
                value = "medium"

            elif value not in {
                "low",
                "medium",
                "high",
            }:
                value = "low"

            rank = confidence_rank[value]

            if rank > best_rank:
                best = value
                best_rank = rank

        return best


__all__ = [
    "ConfidenceCalculator",
]