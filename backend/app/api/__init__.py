"""
TraceIQ - API Package

HTTP API routers for the TraceIQ backend.

Each router is kept in its own module and should remain responsible for:
- Request/response handling
- Authentication/authorization dependencies
- Input validation
- Calling the appropriate service

Business logic must remain in the service layer.
External API communication must remain in integrations.
"""

from __future__ import annotations

__all__: list[str] = []