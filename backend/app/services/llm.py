import json
import httpx
import structlog
from typing import Dict, Any, List
from app.config import settings
from app.rag.prompts import INVESTIGATION_SYSTEM_PROMPT
from app.schemas.evidence import Evidence, TimelineEvent

logger = structlog.get_logger()

class LLMProvider:
    """
    Interface for LLM reasoning.
    Currently defaults to using httpx for an OpenAI-compatible API.
    """
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url or "https://api.openai.com/v1"
        self.model = settings.llm_model
        
    async def analyze(
        self,
        query: str,
        evidence: List[Evidence],
        timeline: List[TimelineEvent],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        if not self.api_key and not settings.demo_mode:
            logger.error("llm_api_key_missing")
            return self._fallback_response()
            
        evidence_json = [e.model_dump(mode='json') for e in evidence]
        timeline_json = [t.model_dump(mode='json') for t in timeline]
        
        user_prompt = (
            f"Incident Query: {query}\n\n"
            f"Context: {json.dumps(context)}\n\n"
            f"Timeline:\n{json.dumps(timeline_json, indent=2)}\n\n"
            f"Evidence:\n{json.dumps(evidence_json, indent=2)}\n"
        )
        
        if settings.demo_mode:
            logger.info("llm_demo_mode_active", returning="deterministic_response")
            return self._demo_response(query, evidence)

        # Real LLM call
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": INVESTIGATION_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.error("llm_call_failed", error=str(e))
            return self._fallback_response()

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "summary": "LLM Analysis unavailable or failed.",
            "likely_causes": [],
            "recommendations": [],
            "follow_up_questions": []
        }
        
    def _demo_response(self, query: str, evidence: List[Evidence]) -> Dict[str, Any]:
        """Deterministic fallback for DEMO_MODE."""
        # Simple heuristic to match demo evidence
        cause = "Authentication middleware update caused audience mismatch."
        evidence_ids = [e.id for e in evidence if "auth" in e.title.lower() or "401" in e.title]
        
        return {
            "summary": "Based on the evidence, the recent authentication middleware update likely caused a spike in 401 errors for legacy clients.",
            "likely_causes": [
                {
                    "cause": cause,
                    "explanation": "Commit 123456 introduced strict audience checking, which caused failures as seen in the 401 metric spike, similar to a historical incident.",
                    "supporting_evidence_ids": evidence_ids,
                    "confidence": "high"
                }
            ],
            "recommendations": [
                {
                    "action": "Revert the strict audience checking in payment-api.",
                    "reason": "Restores access for legacy clients while a proper migration path is designed.",
                    "priority": "high",
                    "supporting_evidence_ids": ["commit_123456", "metric_401_spike"]
                }
            ],
            "follow_up_questions": [
                "Which clients are currently failing authentication?"
            ]
        }
