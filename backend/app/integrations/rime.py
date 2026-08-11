"""
TraceIQ - Rime Voice Integration

Asynchronous adapter for Rime Text-to-Speech.

Responsibilities:
- Convert TraceIQ text responses into speech.
- Handle Rime authentication.
- Reuse HTTP connections.
- Support configurable voice/model/output format.
- Return raw audio bytes to the service/API layer.
- Normalize external failures.

This module does NOT:
- Run investigations.
- Generate investigation responses.
- Contain LLM logic.
- Store audio permanently.
- Expose API routes.

The voice feature is optional. TraceIQ's core investigation pipeline must
continue working when Rime is unavailable or disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.config import Settings, get_settings


# ============================================================================
# TYPES
# ============================================================================


RimeAudioFormat = Literal[
    "mp3",
    "wav",
    "pcm",
    "webm",
]


# ============================================================================
# EXCEPTIONS
# ============================================================================


class RimeIntegrationError(Exception):
    """Base exception for Rime integration failures."""


class RimeConfigurationError(RimeIntegrationError):
    """Raised when Rime is not configured correctly."""


class RimeAuthenticationError(RimeIntegrationError):
    """Raised when Rime authentication fails."""


class RimeRateLimitError(RimeIntegrationError):
    """Raised when Rime rate limits the request."""


class RimeAPIError(RimeIntegrationError):
    """Raised when Rime returns an API error."""


class RimeTimeoutError(RimeIntegrationError):
    """Raised when a Rime request times out."""


# ============================================================================
# RESPONSE MODEL
# ============================================================================


@dataclass(slots=True, frozen=True)
class RimeSynthesisResult:
    """
    Result returned by the Rime TTS client.

    `audio` contains raw bytes returned by Rime.
    """

    audio: bytes
    content_type: str
    model: str
    speaker: str
    character_count: int


# ============================================================================
# CLIENT
# ============================================================================


class RimeClient:
    """
    Async Rime TTS client.

    The HTTP client is reusable so repeated voice requests benefit from
    connection pooling.

    Example:

        async with RimeClient() as rime:
            result = await rime.synthesize(
                "TraceIQ found a likely deployment regression."
            )

            audio = result.audio
    """

    DEFAULT_ENDPOINT = "/v1/rime-tts"

    AUDIO_CONTENT_TYPES: dict[RimeAudioFormat, str] = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "pcm": "audio/L16",
        "webm": "audio/webm;codecs=opus",
    }

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        self._external_client = client is not None
        self._client = client

        if self._client is None:
            timeout = httpx.Timeout(
                timeout=self.settings.rime_timeout_seconds,
                connect=self.settings.http_connect_timeout_seconds,
            )

            limits = httpx.Limits(
                max_connections=self.settings.http_max_connections,
                max_keepalive_connections=(
                    self.settings.http_max_keepalive_connections
                ),
            )

            self._client = httpx.AsyncClient(
                base_url=self.settings.rime_api_url.rstrip("/"),
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                headers=self._build_headers(),
            )

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    async def __aenter__(self) -> "RimeClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the internally owned HTTP client."""

        if self._client is not None and not self._external_client:
            await self._client.aclose()

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def _build_headers(self) -> dict[str, str]:
        """
        Build Rime request headers.

        Authentication is omitted when no key is configured so that the
        client can still be constructed safely in development/tests.
        """

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TraceIQ/1.0",
        }

        if self.settings.rime_api_key:
            api_key = self.settings.rime_api_key.get_secret_value()

            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        return headers

    def _require_configuration(self) -> None:
        """Ensure voice integration is configured before synthesis."""

        if not self.settings.voice_enabled:
            raise RimeConfigurationError(
                "TraceIQ voice functionality is disabled."
            )

        if not self.settings.rime_api_key:
            raise RimeConfigurationError(
                "RIME_API_KEY is not configured."
            )

        if not self.settings.rime_api_url:
            raise RimeConfigurationError(
                "RIME_API_URL is not configured."
            )

    # ========================================================================
    # SYNTHESIS
    # ========================================================================

    async def synthesize(
        self,
        text: str,
        *,
        speaker: str | None = None,
        model: str = "arcana",
        language: str | None = None,
        audio_format: RimeAudioFormat = "mp3",
        sampling_rate: int | None = None,
        speed_alpha: float | None = None,
        pause_between_brackets: bool = False,
        phonemize_between_brackets: bool = False,
        no_text_normalization: bool = False,
    ) -> RimeSynthesisResult:
        """
        Convert text to speech using Rime.

        Rime's current API accepts:
            text
            speaker
            modelId

        Optional parameters are included only when explicitly provided.
        This avoids sending model-specific parameters unnecessarily.
        """

        self._require_configuration()

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError(
                "Text passed to Rime cannot be empty."
            )

        if len(normalized_text) > 100_000:
            raise ValueError(
                "Text passed to Rime is too long."
            )

        normalized_model = model.strip()

        if not normalized_model:
            raise ValueError(
                "Rime model cannot be empty."
            )

        normalized_speaker = (
            speaker.strip()
            if speaker
            else self.settings.rime_voice
        )

        if not normalized_speaker:
            raise ValueError(
                "Rime speaker cannot be empty."
            )

        if audio_format not in self.AUDIO_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported Rime audio format: {audio_format}"
            )

        accept_header = self.AUDIO_CONTENT_TYPES[audio_format]

        payload: dict[str, Any] = {
            "text": normalized_text,
            "speaker": normalized_speaker,
            "modelId": normalized_model,
        }

        if language:
            payload["language"] = language

        if sampling_rate is not None:
            if not 4000 <= sampling_rate <= 44100:
                raise ValueError(
                    "sampling_rate must be between 4000 and 44100."
                )

            payload["samplingRate"] = sampling_rate

        if speed_alpha is not None:
            if speed_alpha <= 0:
                raise ValueError(
                    "speed_alpha must be greater than zero."
                )

            payload["speedAlpha"] = speed_alpha

        if pause_between_brackets:
            payload["pauseBetweenBrackets"] = True

        if phonemize_between_brackets:
            payload["phonemizeBetweenBrackets"] = True

        if no_text_normalization:
            payload["noTextNormalization"] = True

        if self._client is None:
            raise RimeConfigurationError(
                "Rime HTTP client is not initialized."
            )

        headers = {
            "Accept": accept_header,
        }

        try:
            response = await self._client.post(
                self.DEFAULT_ENDPOINT,
                json=payload,
                headers=headers,
            )

        except httpx.TimeoutException as exc:
            raise RimeTimeoutError(
                "Rime TTS request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise RimeAPIError(
                f"Rime TTS request failed: {exc}"
            ) from exc

        if response.status_code in {401, 403}:
            raise RimeAuthenticationError(
                "Rime authentication failed."
            )

        if response.status_code == 429:
            raise RimeRateLimitError(
                "Rime rate limit exceeded."
            )

        if response.status_code >= 400:
            raise RimeAPIError(
                self._format_error(
                    response,
                )
            )

        if not response.content:
            raise RimeAPIError(
                "Rime returned an empty audio response."
            )

        return RimeSynthesisResult(
            audio=response.content,
            content_type=(
                response.headers.get(
                    "content-type",
                    accept_header,
                )
            ),
            model=normalized_model,
            speaker=normalized_speaker,
            character_count=len(normalized_text),
        )

    # ========================================================================
    # STREAMING
    # ========================================================================

    async def stream_synthesis(
        self,
        text: str,
        *,
        speaker: str | None = None,
        model: str = "mistv3",
        language: str | None = None,
        audio_format: RimeAudioFormat = "pcm",
        sampling_rate: int | None = None,
    ):
        """
        Stream synthesized audio chunks from Rime.

        This method is useful for future real-time voice experiences where
        waiting for the complete audio payload would add unnecessary latency.

        The caller owns the response stream lifecycle.
        """

        self._require_configuration()

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError(
                "Text passed to Rime cannot be empty."
            )

        normalized_speaker = (
            speaker.strip()
            if speaker
            else self.settings.rime_voice
        )

        if not normalized_speaker:
            raise ValueError(
                "Rime speaker cannot be empty."
            )

        if audio_format not in self.AUDIO_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported Rime audio format: {audio_format}"
            )

        payload: dict[str, Any] = {
            "text": normalized_text,
            "speaker": normalized_speaker,
            "modelId": model,
        }

        if language:
            payload["language"] = language

        if sampling_rate is not None:
            if not 4000 <= sampling_rate <= 44100:
                raise ValueError(
                    "sampling_rate must be between 4000 and 44100."
                )

            payload["samplingRate"] = sampling_rate

        if self._client is None:
            raise RimeConfigurationError(
                "Rime HTTP client is not initialized."
            )

        accept_header = self.AUDIO_CONTENT_TYPES[audio_format]

        try:
            request = self._client.build_request(
                "POST",
                self.DEFAULT_ENDPOINT,
                json=payload,
                headers={
                    "Accept": accept_header,
                },
            )

            response = await self._client.send(
                request,
                stream=True,
            )

        except httpx.TimeoutException as exc:
            raise RimeTimeoutError(
                "Rime streaming request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise RimeAPIError(
                f"Rime streaming request failed: {exc}"
            ) from exc

        if response.status_code in {401, 403}:
            await response.aclose()

            raise RimeAuthenticationError(
                "Rime authentication failed."
            )

        if response.status_code == 429:
            await response.aclose()

            raise RimeRateLimitError(
                "Rime rate limit exceeded."
            )

        if response.status_code >= 400:
            error = await response.aread()
            await response.aclose()

            raise RimeAPIError(
                f"Rime streaming request failed with HTTP "
                f"{response.status_code}: "
                f"{error.decode('utf-8', errors='replace')[:1000]}"
            )

        return response

    # ========================================================================
    # ERROR HANDLING
    # ========================================================================

    @staticmethod
    def _format_error(
        response: httpx.Response,
    ) -> str:
        """Build a safe, bounded Rime API error message."""

        try:
            data = response.json()

            if isinstance(data, dict):
                message = (
                    data.get("message")
                    or data.get("error")
                    or data.get("detail")
                )

                if isinstance(message, str) and message.strip():
                    return (
                        f"Rime API returned HTTP "
                        f"{response.status_code}: "
                        f"{message.strip()[:1000]}"
                    )

        except ValueError:
            pass

        return (
            f"Rime API returned HTTP "
            f"{response.status_code}: "
            f"{response.text[:1000]}"
        )


# ============================================================================
# FACTORY
# ============================================================================


def create_rime_client(
    settings: Settings | None = None,
) -> RimeClient:
    """
    Create a Rime client using application settings.
    """

    return RimeClient(
        settings=settings or get_settings(),
    )


__all__ = [
    "RimeClient",
    "RimeSynthesisResult",
    "RimeIntegrationError",
    "RimeConfigurationError",
    "RimeAuthenticationError",
    "RimeRateLimitError",
    "RimeAPIError",
    "RimeTimeoutError",
    "create_rime_client",
]