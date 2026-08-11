"""
TraceIQ - Investigation API

Primary API endpoint for TraceIQ incident investigation.

Flow:

    Client
      │
      ▼
    FastAPI
      │
      ├── Request validation
      ├── Rate limiting
      │
      ▼
    InvestigationOrchestrator
      │
      ├── Evidence collection
      ├── Retrieval / RAG
      ├── Correlation
      ├── LLM reasoning
      ├── Validation
      ├── Confidence assessment
      └── Recommendations
      │
      ▼
    InvestigationResponse

This router intentionally contains no investigation business logic.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.rate_limit import rate_limit_middleware
from app.schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse,
)
from app.services.orchestrator import InvestigationOrchestrator


logger = structlog.get_logger(__name__)


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


# ============================================================================
# DEPENDENCIES
# ============================================================================


_orchestrator: InvestigationOrchestrator | None = None


def get_orchestrator() -> InvestigationOrchestrator:
    """
    Return the application investigation orchestrator.

    The singleton is created lazily rather than during module import.

    This avoids expensive initialization during:
    - CLI imports
    - Test collection
    - OpenAPI generation
    - Worker startup
    """

    global _orchestrator

    if _orchestrator is None:
        _orchestrator = InvestigationOrchestrator()

    return _orchestrator


# ============================================================================
# INVESTIGATION ENDPOINT
# ============================================================================


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Investigate an incident",
    description=(
        "Analyze an engineering incident using available evidence from "
        "connected engineering and observability systems."
    ),
    dependencies=[
        Depends(rate_limit_middleware),
    ],
)
async def investigate_endpoint(
    request: InvestigationRequest,
    orch: Annotated[
        InvestigationOrchestrator,
        Depends(get_orchestrator),
    ],
) -> InvestigationResponse:
    """
    Process an engineer's investigation request.

    The orchestrator is responsible for the complete investigation pipeline.

    The API layer only:
    1. Receives the validated request.
    2. Performs lightweight validation.
    3. Invokes the orchestrator.
    4. Returns the structured investigation response.
    """

    # ------------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------------

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Investigation query cannot be empty.",
        )

    # Pydantic already validates the request model, but we normalize the
    # query here so downstream services never receive accidental whitespace.
    request.query = query

    # ------------------------------------------------------------------------
    # Structured request logging
    # ------------------------------------------------------------------------

    log = logger.bind(
        incident_id=request.incident_id,
        service=request.service,
        severity=(
            request.severity.value
            if request.severity is not None
            else None
        ),
        conversation_id=request.conversation_id,
    )

    log.info(
        "investigation_request_received",
        query_length=len(query),
    )

    # ------------------------------------------------------------------------
    # Investigation
    # ------------------------------------------------------------------------

    try:
        response = await orch.investigate(request)

    except HTTPException:
        raise

    except ValueError as exc:
        log.warning(
            "investigation_validation_failed",
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except TimeoutError as exc:
        log.error(
            "investigation_timeout",
            error=str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Investigation timed out. Please try again.",
        ) from exc

    except Exception:
        log.exception(
            "investigation_endpoint_error",
        )

        # Do not expose internal exception details to the client.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete investigation.",
        ) from None

    # ------------------------------------------------------------------------
    # Response logging
    # ------------------------------------------------------------------------

    log.info(
        "investigation_request_completed",
        request_id=response.request_id,
        evidence_count=len(response.evidence),
        timeline_event_count=len(response.timeline),
        likely_cause_count=len(response.likely_causes),
        recommendation_count=len(response.recommendations),
        confidence=response.confidence.level.value,
    )

    return response


# ============================================================================
# BACKWARD-COMPATIBLE ROUTE
# ============================================================================


@router.post(
    "/investigate",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Investigate an incident",
    description=(
        "Backward-compatible investigation endpoint. "
        "Use POST /investigations for the preferred API contract."
    ),
    dependencies=[
        Depends(rate_limit_middleware),
    ],
    include_in_schema=True,
)
async def investigate_legacy_endpoint(
    request: InvestigationRequest,
    orch: Annotated[
        InvestigationOrchestrator,
        Depends(get_orchestrator),
    ],
) -> InvestigationResponse:
    """
    Backward-compatible endpoint.

    Existing frontend/demo clients may already call:

        POST /investigate

    If the router is mounted under `/api/v1`, this becomes:

        POST /api/v1/investigations/investigate

    The actual implementation is shared with the primary endpoint.
    """

    return await investigate_endpoint(
        request=request,
        orch=orch,
    )


__all__ = [
    "router",
    "get_orchestrator",
    "investigate_endpoint",
    "investigate_legacy_endpoint",
]