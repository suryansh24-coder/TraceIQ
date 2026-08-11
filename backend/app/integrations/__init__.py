"""
TraceIQ - External Integrations

This package contains adapters for external systems used by TraceIQ.

Integrations should:
- Handle external API communication.
- Normalize provider-specific responses.
- Keep provider details out of the service layer.
- Use asynchronous I/O where supported.
- Never contain investigation/business orchestration logic.

Available integrations include:
- GitHub
- GitHub Actions
- Monitoring
- Rime voice services
"""

from __future__ import annotations

__all__: list[str] = []