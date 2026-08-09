from app.services.evidence_builder import EvidenceBuilder
from app.services.incident_timeline import IncidentTimeline
from app.services.evidence_validator import EvidenceValidator
from app.schemas.evidence import Evidence
from datetime import datetime, timezone

def test_evidence_builder_deduplication():
    builder = EvidenceBuilder()
    
    ev1 = Evidence(id="1", source="test", title="T1", content="C1", evidence_type="log")
    ev2 = Evidence(id="1", source="test", title="T1", content="C1", evidence_type="log")
    ev3 = Evidence(id="2", source="test", title="T2", content="C2", evidence_type="log")
    
    unified = builder.build([ev1, ev2, ev3])
    
    assert len(unified) == 2
    assert {e.id for e in unified} == {"1", "2"}

def test_incident_timeline_sorting():
    timeline_builder = IncidentTimeline()
    
    ev1 = Evidence(id="1", source="test", title="Late", content="C1", evidence_type="log", timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc))
    ev2 = Evidence(id="2", source="test", title="Early", content="C2", evidence_type="log", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    
    timeline = timeline_builder.build([ev1, ev2])
    
    assert len(timeline) == 2
    assert timeline[0].description == "Early"
    assert timeline[1].description == "Late"

def test_evidence_validator_removes_hallucinations():
    validator = EvidenceValidator()
    
    llm_response = {
        "summary": "Test",
        "likely_causes": [
            {
                "cause": "Real Cause",
                "explanation": "Exp",
                "supporting_evidence_ids": ["real_id"],
                "confidence": "high"
            },
            {
                "cause": "Fake Cause",
                "explanation": "Exp",
                "supporting_evidence_ids": ["hallucinated_id"],
                "confidence": "high"
            }
        ]
    }
    
    provided_evidence = [
        Evidence(id="real_id", source="test", title="T1", content="C1", evidence_type="log")
    ]
    
    validated = validator.validate(llm_response, provided_evidence)
    
    assert len(validated["likely_causes"]) == 1
    assert validated["likely_causes"][0]["cause"] == "Real Cause"
