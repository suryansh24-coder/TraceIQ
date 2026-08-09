import structlog
from typing import Dict, Any
import time

from app.schemas.investigation import InvestigationRequest, InvestigationResponse
from app.utils.sanitization import sanitize_query
from app.config import settings

from app.services.llm import LLMProvider
from app.services.demo_mode import DemoProvider
from app.services.evidence_builder import EvidenceBuilder
from app.services.incident_timeline import IncidentTimeline
from app.services.evidence_validator import EvidenceValidator
from app.services.confidence import ConfidenceCalculator
from app.services.recommendation import RecommendationEngine
from app.services.report_generator import ReportGenerator

logger = structlog.get_logger()

class InvestigationOrchestrator:
    """
    The core pipeline orchestrating the voice-first incident investigation.
    """
    def __init__(self):
        self.llm = LLMProvider()
        self.demo_provider = DemoProvider()
        self.evidence_builder = EvidenceBuilder()
        self.timeline_builder = IncidentTimeline()
        self.validator = EvidenceValidator()
        self.confidence_calc = ConfidenceCalculator()
        self.rec_engine = RecommendationEngine()
        self.report_gen = ReportGenerator()

    async def investigate(self, request: InvestigationRequest) -> InvestigationResponse:
        start_time = time.time()
        logger.info("investigation_started", query=request.query)

        # 1. Sanitize
        clean_query = sanitize_query(request.query)

        # 2. Collect Evidence (Demo fallback or real)
        if settings.demo_mode:
            raw_evidence = await self.demo_provider.get_evidence()
        else:
            # TODO: Integrate with actual EngineeringContextProvider and KnowledgeRetriever
            raw_evidence = []
            
        # 3. Build Unified Evidence
        unified_evidence = self.evidence_builder.build(raw_evidence)
        
        # 4. Build Timeline
        timeline = self.timeline_builder.build(unified_evidence)
        
        # 5. LLM Reasoning
        context = {
            "incident_id": request.incident_id,
            "service": request.service,
            "severity": request.severity.value if request.severity else None
        }
        raw_llm_response = await self.llm.analyze(clean_query, unified_evidence, timeline, context)
        
        # 6. Validate
        validated_response = self.validator.validate(raw_llm_response, unified_evidence)
        
        # 7. Confidence & Recommendations
        confidence = self.confidence_calc.calculate(validated_response, unified_evidence)
        recommendations = self.rec_engine.generate(validated_response)
        
        # 8. Generate Report
        response = self.report_gen.generate(
            request=request,
            validated_llm_response=validated_response,
            unified_evidence=unified_evidence,
            timeline=timeline,
            confidence=confidence,
            recommendations=recommendations
        )
        
        # Update metadata
        processing_time_ms = int((time.time() - start_time) * 1000)
        response.processing_metadata["duration_ms"] = processing_time_ms
        response.processing_metadata["demo_mode"] = settings.demo_mode
        
        logger.info("investigation_completed", duration_ms=processing_time_ms, request_id=response.request_id)
        return response
