import pytest
from app.services.orchestrator import InvestigationOrchestrator
from app.schemas.investigation import InvestigationRequest
from app.config import settings
import os

@pytest.fixture
def orchestrator():
    # Force demo mode for tests
    settings.demo_mode = True
    return InvestigationOrchestrator()

@pytest.mark.asyncio
async def test_investigation_demo_mode(orchestrator):
    request = InvestigationRequest(
        query="Why is the Payment API returning authentication errors?",
        service="payment-api",
        severity="high"
    )
    
    response = await orchestrator.investigate(request)
    
    assert response.request_id is not None
    assert response.service == "payment-api"
    assert len(response.evidence) > 0
    assert len(response.timeline) > 0
    assert len(response.likely_causes) > 0
    
    # Ensure evidence IDs are tracked properly
    cause_evidence_ids = response.likely_causes[0].supporting_evidence_ids
    assert len(cause_evidence_ids) > 0
    for eid in cause_evidence_ids:
        assert any(e.id == eid for e in response.evidence)

@pytest.mark.asyncio
async def test_investigation_demo_fallback(orchestrator):
    """
    Test that if LLM is unavailable in non-demo mode, it falls back safely.
    """
    settings.demo_mode = False
    
    # This shouldn't raise an exception but return a safe fallback structure
    request = InvestigationRequest(query="Some issue")
    response = await orchestrator.investigate(request)
    
    assert "LLM Analysis unavailable" in response.summary or response.summary == "Insufficient evidence to determine a reliable root cause."
    
    # Reset
    settings.demo_mode = True
