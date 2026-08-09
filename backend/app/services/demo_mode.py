import json
import os
from typing import List, Dict, Any
from app.schemas.evidence import Evidence
import structlog

logger = structlog.get_logger()

class DemoProvider:
    """
    Deterministic provider for DEMO_MODE.
    Loads synthetic data from demo/scenario.json.
    """
    def __init__(self):
        self.scenario_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "demo",
            "scenario.json"
        )
        self._load_scenario()

    def _load_scenario(self):
        try:
            with open(self.scenario_file, 'r') as f:
                self.scenario_data = json.load(f)
                logger.info("demo_scenario_loaded", path=self.scenario_file)
        except Exception as e:
            logger.error("demo_scenario_load_failed", error=str(e))
            self.scenario_data = {"evidence": []}

    async def get_evidence(self) -> List[Evidence]:
        """Return deterministic evidence for the demo."""
        evidence_list = []
        for item in self.scenario_data.get("evidence", []):
            try:
                evidence = Evidence(**item)
                evidence_list.append(evidence)
            except Exception as e:
                logger.error("demo_evidence_validation_failed", item=item, error=str(e))
        return evidence_list
