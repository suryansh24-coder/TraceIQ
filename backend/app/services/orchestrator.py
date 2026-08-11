"""
TraceIQ - Investigation Orchestrator

Central orchestration layer for the TraceIQ investigation pipeline.

Pipeline:

    Request
       ↓
    Sanitization
       ↓
    Evidence Collection
       ↓
    Evidence Builder
       ↓
    Timeline Builder
       ↓
    LLM Reasoning
       ↓
    Evidence Validation
       ↓
    Confidence Calculation
       ↓
    Recommendation Engine
       ↓
    Report Generator
       ↓
    InvestigationResponse

The orchestrator coordinates services but does not implement their internal
business logic.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from app.config import get_settings
from app.schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse,
)

from app.services.confidence import ConfidenceCalculator
from app.services.demo_mode import DemoProvider
from app.services.evidence_builder import EvidenceBuilder
from app.services.evidence_validator import EvidenceValidator
from app.services.incident_timeline import IncidentTimeline
from app.services.llm import LLMProvider
from app.services.recommendation import RecommendationEngine
from app.services.report_generator import ReportGenerator
from app.utils.sanitization import sanitize_query


logger = structlog.get_logger(__name__)


class InvestigationOrchestrator:
    """
    Core TraceIQ investigation pipeline.

    A single orchestrator instance is intended to be reused by the FastAPI
    application so its service dependencies can also be reused efficiently.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

        # --------------------------------------------------------------------
        # Core services
        # --------------------------------------------------------------------

        self.llm = LLMProvider(
            settings=self.settings,
        )

        self.demo_provider = DemoProvider()

        self.evidence_builder = EvidenceBuilder()

        self.timeline_builder = IncidentTimeline()

        self.validator = EvidenceValidator()

        self.confidence_calculator = ConfidenceCalculator()

        self.recommendation_engine = RecommendationEngine()

        self.report_generator = ReportGenerator()

    # ========================================================================
    # MAIN INVESTIGATION PIPELINE
    # ========================================================================

    async def investigate(
        self,
        request: InvestigationRequest,
    ) -> InvestigationResponse:
        """
        Execute a complete TraceIQ investigation.

        The pipeline is intentionally sequential between stages because each
        stage consumes the validated output of the previous stage.
        """

        start_time = time.monotonic()

        request_id = (
            request.conversation_id
            or "investigation"
        )

        logger.info(
            "investigation_started",
            conversation_id=request.conversation_id,
            incident_id=request.incident_id,
            service=request.service,
            severity=(
                request.severity.value
                if request.severity
                else None
            ),
        )

        try:
            # ================================================================
            # 1. SANITIZE REQUEST
            # ================================================================

            clean_query = sanitize_query(
                request.query,
            )

            if not clean_query.strip():
                raise ValueError(
                    "Investigation query cannot be empty."
                )

            # ================================================================
            # 2. COLLECT EVIDENCE
            # ================================================================

            raw_evidence = await self._collect_evidence(
                request=request,
                clean_query=clean_query,
            )

            logger.info(
                "investigation_evidence_collected",
                evidence_count=len(raw_evidence),
            )

            # ================================================================
            # 3. UNIFY / DEDUPLICATE / RANK EVIDENCE
            # ================================================================

            unified_evidence = self.evidence_builder.build(
                raw_evidence,
            )

            logger.info(
                "investigation_evidence_unified",
                evidence_count=len(unified_evidence),
            )

            # ================================================================
            # 4. BUILD TIMELINE
            # ================================================================

            timeline = self.timeline_builder.build(
                unified_evidence,
            )

            logger.info(
                "investigation_timeline_built",
                timeline_count=len(timeline),
            )

            # ================================================================
            # 5. BUILD LLM CONTEXT
            # ================================================================

            context = self._build_llm_context(
                request=request,
                clean_query=clean_query,
            )

            # ================================================================
            # 6. LLM REASONING
            # ================================================================

            raw_llm_response = await self._run_llm_analysis(
                clean_query=clean_query,
                evidence=unified_evidence,
                timeline=timeline,
                context=context,
            )

            # ================================================================
            # 7. EVIDENCE VALIDATION
            # ================================================================

            validated_response = self.validator.validate(
                raw_llm_response,
                unified_evidence,
            )

            logger.info(
                "investigation_response_validated",
                grounded=(
                    validated_response
                    .get("_validation", {})
                    .get("grounded", False)
                    if isinstance(
                        validated_response.get(
                            "_validation",
                            {},
                        ),
                        dict,
                    )
                    else False
                ),
            )

            # ================================================================
            # 8. CONFIDENCE
            # ================================================================

            confidence = self.confidence_calculator.calculate(
                validated_response,
                unified_evidence,
            )

            # ================================================================
            # 9. RECOMMENDATIONS
            # ================================================================

            recommendations = (
                self.recommendation_engine.generate(
                    validated_response,
                )
            )

            # ================================================================
            # 10. FINAL REPORT
            # ================================================================

            response = self.report_generator.generate(
                request=request,
                validated_llm_response=validated_response,
                unified_evidence=unified_evidence,
                timeline=timeline,
                confidence=confidence,
                recommendations=recommendations,
            )

            # ================================================================
            # 11. PROCESSING METADATA
            # ================================================================

            duration_ms = int(
                (
                    time.monotonic()
                    - start_time
                )
                * 1000
            )

            response.processing_metadata.update(
                {
                    "duration_ms": duration_ms,
                    "demo_mode": self.settings.demo_mode,
                    "llm_provider": (
                        self.settings.llm_provider
                    ),
                    "llm_model": self.settings.llm_model,
                    "evidence_count": len(
                        unified_evidence,
                    ),
                    "timeline_event_count": len(
                        timeline,
                    ),
                    "source_count": len(
                        response.sources,
                    ),
                }
            )

            logger.info(
                "investigation_completed",
                request_id=response.request_id,
                duration_ms=duration_ms,
                evidence_count=len(
                    unified_evidence,
                ),
                timeline_count=len(
                    timeline,
                ),
                confidence=response.confidence.level.value,
                confidence_score=response.confidence.score,
            )

            return response

        except asyncio.TimeoutError:
            duration_ms = self._duration_ms(
                start_time,
            )

            logger.error(
                "investigation_timeout",
                duration_ms=duration_ms,
                incident_id=request.incident_id,
                service=request.service,
            )

            raise

        except Exception:
            duration_ms = self._duration_ms(
                start_time,
            )

            logger.exception(
                "investigation_failed",
                duration_ms=duration_ms,
                incident_id=request.incident_id,
                service=request.service,
            )

            raise

    # ========================================================================
    # EVIDENCE COLLECTION
    # ========================================================================

    async def _collect_evidence(
        self,
        *,
        request: InvestigationRequest,
        clean_query: str,
    ) -> list[Any]:
        """
        Collect investigation evidence.

        DEMO_MODE uses the deterministic demo provider.

        Real integrations will be connected here as their service interfaces
        are finalized. We intentionally do not fabricate production evidence.
        """

        if self.settings.demo_mode:
            return await self.demo_provider.get_evidence()

        # --------------------------------------------------------------------
        # Production integration boundary
        # --------------------------------------------------------------------
        #
        # GitHub, monitoring, and RAG providers will be connected here once
        # their actual service interfaces are available.
        #
        # Returning an empty list is preferable to fabricating evidence.
        #
        # --------------------------------------------------------------------

        logger.warning(
            "production_evidence_providers_not_connected",
            incident_id=request.incident_id,
            service=request.service,
            query_length=len(clean_query),
        )

        return []

    # ========================================================================
    # LLM ANALYSIS
    # ========================================================================

    async def _run_llm_analysis(
        self,
        *,
        clean_query: str,
        evidence: list[Any],
        timeline: list[Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run LLM reasoning under the configured investigation timeout.
        """

        timeout = self.settings.investigation_timeout_seconds

        try:
            return await asyncio.wait_for(
                self.llm.analyze(
                    clean_query,
                    evidence,
                    timeline,
                    context,
                ),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            logger.error(
                "llm_investigation_timeout",
                timeout_seconds=timeout,
            )

            return {
                "summary": (
                    "LLM analysis timed out before a reliable "
                    "investigation could be completed."
                ),
                "likely_causes": [],
                "recommendations": [],
                "follow_up_questions": [
                    (
                        "Would you like to retry the investigation?"
                    ),
                ],
            }

    # ========================================================================
    # LLM CONTEXT
    # ========================================================================

    @staticmethod
    def _build_llm_context(
        *,
        request: InvestigationRequest,
        clean_query: str,
    ) -> dict[str, Any]:
        """
        Build a controlled context object for the LLM.

        User-provided context is copied rather than directly modifying the
        incoming Pydantic model.
        """

        context: dict[str, Any] = {
            "incident_id": request.incident_id,
            "service": request.service,
            "severity": (
                request.severity.value
                if request.severity
                else None
            ),
            "conversation_id": request.conversation_id,
            "query": clean_query,
        }

        # Add user-provided context while protecting the core fields above.
        if isinstance(
            request.context,
            dict,
        ):
            for key, value in request.context.items():
                normalized_key = str(
                    key,
                ).strip()

                if not normalized_key:
                    continue

                if normalized_key in context:
                    continue

                if len(context) >= 50:
                    break

                context[normalized_key] = value

        return context

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def close(self) -> None:
        """
        Release resources owned by the orchestrator.

        This should be called during FastAPI application shutdown.
        """

        try:
            await self.llm.aclose()
        except Exception:
            logger.exception(
                "orchestrator_shutdown_failed",
            )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _duration_ms(
        start_time: float,
    ) -> int:
        """Calculate elapsed processing time."""

        return int(
            (
                time.monotonic()
                - start_time
            )
            * 1000
        )


__all__ = [
    "InvestigationOrchestrator",
]