"""
TraceIQ API Schemas.

This package contains the Pydantic models used for:
- API request validation
- API response serialization
- Investigation workflows
- Evidence and confidence modeling
- Engineering/incident data
- Voice interactions

Keep this module free of business logic.

Schemas should be imported from their dedicated modules, for example:

    from app.schemas.common import APIResponse
    from app.schemas.investigation import InvestigationRequest
"""

from __future__ import annotations

__all__: list[str] = []