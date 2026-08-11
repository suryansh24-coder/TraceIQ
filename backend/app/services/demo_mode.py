"""
TraceIQ - Demo Mode Provider

Deterministic evidence provider used when DEMO_MODE is enabled.

The provider loads synthetic incident evidence from:

    TraceIQ/demo/scenario.json

Responsibilities:
- Load the demo scenario safely.
- Validate evidence against the Evidence schema.
- Return deterministic evidence.
- Never call external services.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from app.config import get_settings
from app.schemas.evidence import Evidence


logger = structlog.get_logger(__name__)


class DemoProvider:
    """
    Deterministic provider for TraceIQ demo mode.
    """

    def __init__(
        self,
        scenario_file: str | None = None,
    ) -> None:
        settings = get_settings()

        if scenario_file:
            self.scenario_file = Path(
                scenario_file,
            ).expanduser().resolve()
        else:
            self.scenario_file = self._resolve_scenario_file(
                settings.demo_data_path,
                settings.demo_scenario_file,
            )

        self.scenario_data: dict[str, Any] = {
            "evidence": [],
        }

        self._load_scenario()

    # ========================================================================
    # SCENARIO PATH
    # ========================================================================

    @staticmethod
    def _resolve_scenario_file(
        demo_data_path: str,
        scenario_file: str,
    ) -> Path:
        """
        Resolve the demo scenario path.

        The preferred location is:

            TraceIQ/demo/scenario.json

        The configured demo path is also respected when supplied.
        """

        current_file = Path(__file__).resolve()

        # backend/app/services/demo_mode.py
        # parents:
        #   0 -> services
        #   1 -> app
        #   2 -> backend
        #   3 -> TraceIQ
        project_root = current_file.parents[3]

        configured_path = Path(
            demo_data_path,
        ).expanduser()

        if not configured_path.is_absolute():
            configured_path = (
                project_root / configured_path
            ).resolve()

        if configured_path.is_file():
            return configured_path

        return (
            configured_path / scenario_file
        ).resolve()

    # ========================================================================
    # LOAD SCENARIO
    # ========================================================================

    def _load_scenario(self) -> None:
        """
        Load and validate the scenario JSON.

        A malformed or missing demo file does not crash application startup.
        The provider instead exposes an empty evidence set.
        """

        if not self.scenario_file.exists():
            logger.error(
                "demo_scenario_file_not_found",
                path=str(self.scenario_file),
            )

            self.scenario_data = {
                "evidence": [],
            }

            return

        if not self.scenario_file.is_file():
            logger.error(
                "demo_scenario_path_not_file",
                path=str(self.scenario_file),
            )

            self.scenario_data = {
                "evidence": [],
            }

            return

        try:
            with self.scenario_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except json.JSONDecodeError as exc:
            logger.error(
                "demo_scenario_invalid_json",
                path=str(self.scenario_file),
                error=str(exc),
            )

            self.scenario_data = {
                "evidence": [],
            }

            return

        except OSError as exc:
            logger.error(
                "demo_scenario_read_failed",
                path=str(self.scenario_file),
                error=str(exc),
            )

            self.scenario_data = {
                "evidence": [],
            }

            return

        if not isinstance(data, dict):
            logger.error(
                "demo_scenario_invalid_root",
                path=str(self.scenario_file),
            )

            self.scenario_data = {
                "evidence": [],
            }

            return

        evidence = data.get(
            "evidence",
            [],
        )

        if not isinstance(evidence, list):
            logger.error(
                "demo_scenario_evidence_invalid",
                path=str(self.scenario_file),
            )

            evidence = []

        self.scenario_data = {
            **data,
            "evidence": evidence,
        }

        logger.info(
            "demo_scenario_loaded",
            path=str(self.scenario_file),
            evidence_count=len(evidence),
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def get_evidence(self) -> list[Evidence]:
        """
        Return deterministic validated evidence from the demo scenario.
        """

        evidence_list: list[Evidence] = []

        raw_evidence = self.scenario_data.get(
            "evidence",
            [],
        )

        if not isinstance(
            raw_evidence,
            list,
        ):
            return []

        for index, item in enumerate(
            raw_evidence,
        ):
            if not isinstance(
                item,
                dict,
            ):
                logger.warning(
                    "demo_evidence_invalid_item",
                    index=index,
                )
                continue

            try:
                evidence = Evidence.model_validate(
                    item,
                )

            except Exception as exc:
                logger.error(
                    "demo_evidence_validation_failed",
                    index=index,
                    evidence_id=item.get("id"),
                    error=str(exc),
                )
                continue

            evidence_list.append(
                evidence,
            )

        logger.info(
            "demo_evidence_loaded",
            evidence_count=len(evidence_list),
        )

        return evidence_list

    async def get_scenario_metadata(
        self,
    ) -> dict[str, Any]:
        """
        Return non-evidence scenario metadata.

        Evidence itself is intentionally excluded to prevent callers from
        bypassing the Evidence schema.
        """

        return {
            key: value
            for key, value in self.scenario_data.items()
            if key != "evidence"
        }

    async def reload(self) -> None:
        """
        Reload the scenario from disk.

        Useful during development when the demo scenario is edited while
        the API remains running.
        """

        self._load_scenario()


__all__ = [
    "DemoProvider",
]