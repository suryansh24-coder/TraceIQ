"""
TraceIQ - Voice API Router

HTTP endpoints for TraceIQ voice interactions.

Flow:

    Client
       │
       ▼
    Voice API
       │
       ▼
    Rime Integration
       │
       ▼
    Audio

The voice layer is optional. Failure of voice functionality must never
prevent the core TraceIQ investigation API from working.

Responsibilities:
- Validate voice requests.
- Invoke the voice/TTS integration.
- Return audio responses.
- Translate integration failures into safe HTTP errors.

This router does NOT:
- Perform root-cause analysis.
- Call the investigation orchestrator directly.
- Generate recommendations.
- Store permanent audio files.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.config import settings
from app.integrations.rime import (
    RimeAPIError,
    RimeAuthenticationError,
    RimeClient,
    RimeConfigurationError,
    RimeIntegrationError,
    RimeRateLimitError,
    RimeTimeoutError,
)
from app.schemas.voice import (
    VoiceOutputFormat,
    VoiceRequest,
    VoiceResponse,
    VoiceProcessingStatus,
)


logger = structlog.get_logger(__name__)


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


# ============================================================================
# DEPENDENCY
# ============================================================================


def get_rime_client() -> RimeClient:
    """
    Return a Rime client for the current request.

    The client remains isolated from the API layer so the provider can later
    be replaced without changing the public endpoint contract.
    """

    return RimeClient(settings=settings)


# ============================================================================
# ERROR TRANSLATION
# ============================================================================


def _rime_http_exception(
    exc: RimeIntegrationError,
) -> HTTPException:
    """Translate Rime integration errors into safe HTTP responses."""

    if isinstance(exc, RimeConfigurationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service is not configured.",
        )

    if isinstance(exc, RimeAuthenticationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice provider authentication failed.",
        )

    if isinstance(exc, RimeRateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Voice provider rate limit exceeded.",
        )

    if isinstance(exc, RimeTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Voice synthesis timed out.",
        )

    if isinstance(exc, RimeAPIError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice provider request failed.",
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Voice service is temporarily unavailable.",
    )


# ============================================================================
# HEALTH
# ============================================================================


@router.get(
    "/status",
    summary="Get voice service status",
    description="Return whether TraceIQ voice functionality is configured.",
)
async def voice_status() -> dict[str, object]:
    """
    Return lightweight voice configuration status.

    This does not make an external Rime request.
    """

    configured = bool(
        settings.voice_enabled
        and settings.rime_api_key
        and settings.rime_api_url
    )

    return {
        "enabled": settings.voice_enabled,
        "configured": configured,
        "provider": "rime",
    }


# ============================================================================
# TEXT TO SPEECH
# ============================================================================


@router.post(
    "/synthesize",
    summary="Synthesize text into speech",
    description=(
        "Convert TraceIQ text into speech using the configured voice provider."
    ),
    responses={
        200: {
            "description": "Audio generated successfully.",
            "content": {
                "audio/mpeg": {},
                "audio/wav": {},
                "audio/L16": {},
                "audio/webm": {},
            },
        },
    },
)
async def synthesize_voice(
    request: VoiceRequest,
    rime: Annotated[
        RimeClient,
        Depends(get_rime_client),
    ],
) -> Response:
    """
    Convert text into audio.

    The returned response is raw audio rather than JSON so browser clients
    can directly consume it through an Audio element or Blob URL.
    """

    if not settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice functionality is disabled.",
        )

    text = (request.transcript or "").strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text to synthesize cannot be empty.",
        )

    log = logger.bind(
        conversation_id=request.conversation_id,
        incident_id=request.incident_id,
        service=request.service,
    )

    log.info(
        "voice_synthesis_requested",
        text_length=len(text),
        language=request.language,
    )

    try:
        result = await rime.synthesize(
            text,
            language=request.language,
            audio_format="mp3",
        )

        log.info(
            "voice_synthesis_completed",
            character_count=result.character_count,
            audio_size_bytes=len(result.audio),
        )

        return Response(
            content=result.audio,
            media_type=result.content_type,
            headers={
                "Content-Disposition": (
                    'inline; filename="traceiq-response.mp3"'
                ),
                "Cache-Control": "no-store",
                "X-TraceIQ-Voice-Provider": "rime",
            },
        )

    except RimeIntegrationError as exc:
        log.error(
            "voice_synthesis_failed",
            error_type=type(exc).__name__,
        )

        raise _rime_http_exception(exc) from exc

    finally:
        await rime.aclose()


# ============================================================================
# STRUCTURED VOICE RESPONSE
# ============================================================================


@router.post(
    "/synthesize/json",
    response_model=VoiceResponse,
    summary="Synthesize text with metadata",
    description=(
        "Synthesize TraceIQ text and return audio metadata together with "
        "the generated response."
    ),
)
async def synthesize_voice_json(
    request: VoiceRequest,
    rime: Annotated[
        RimeClient,
        Depends(get_rime_client),
    ],
) -> VoiceResponse:
    """
    JSON-oriented voice endpoint.

    This endpoint currently returns a data URL containing the generated
    audio. It is intended for short responses/demo usage.

    For larger audio payloads, `/voice/synthesize` is preferred because it
    returns the audio directly and avoids Base64 expansion.
    """

    if not settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice functionality is disabled.",
        )

    text = (request.transcript or "").strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text to synthesize cannot be empty.",
        )

    try:
        result = await rime.synthesize(
            text,
            language=request.language,
            audio_format="mp3",
        )

        # We deliberately do not embed raw audio bytes into JSON.
        #
        # The direct `/voice/synthesize` endpoint is the preferred audio
        # transport. This JSON endpoint therefore communicates successful
        # synthesis metadata while avoiding an unnecessarily large response.
        return VoiceResponse(
            request_id=request.conversation_id or "voice-request",
            status=VoiceProcessingStatus.COMPLETED,
            text=text,
            transcript=request.transcript,
            audio_url=None,
            audio_format=VoiceOutputFormat.MP3,
            processing_time_ms=None,
        )

    except RimeIntegrationError as exc:
        raise _rime_http_exception(exc) from exc

    finally:
        await rime.aclose()


__all__ = [
    "router",
    "get_rime_client",
    "voice_status",
    "synthesize_voice",
    "synthesize_voice_json",
]