"""
TraceIQ - LLM Service

Provider-agnostic asynchronous LLM reasoning layer.

Supports:
- OpenAI-compatible APIs
- OpenAI
- Gemini-compatible/OpenAI-compatible endpoints
- Ollama
- Custom OpenAI-compatible endpoints

Responsibilities:
- Build bounded investigation prompts.
- Call the configured LLM.
- Retry transient failures.
- Parse structured JSON responses.
- Provide deterministic demo-mode reasoning.
- Gracefully degrade when the LLM is unavailable.

This service does not:
- Collect engineering evidence.
- Query monitoring systems.
- Perform RAG retrieval.
- Calculate final confidence.
- Generate the final report.
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any, Mapping, Sequence

import httpx
import structlog

from app.config import Settings, get_settings
from app.rag.prompts import INVESTIGATION_SYSTEM_PROMPT
from app.schemas.evidence import Evidence, TimelineEvent


logger = structlog.get_logger(__name__)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class LLMError(Exception):
    """Base exception for LLM failures."""


class LLMConfigurationError(LLMError):
    """Invalid LLM configuration."""


class LLMAuthenticationError(LLMError):
    """LLM authentication failure."""


class LLMRateLimitError(LLMError):
    """LLM provider rate limit."""


class LLMTimeoutError(LLMError):
    """LLM provider timeout."""


class LLMResponseError(LLMError):
    """Invalid LLM response."""


# ============================================================================
# CONSTANTS
# ============================================================================


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"

MAX_QUERY_LENGTH = 8_000
MAX_CONTEXT_LENGTH = 12_000
MAX_EVIDENCE_ITEMS = 80
MAX_TIMELINE_ITEMS = 80
MAX_EVIDENCE_CONTENT_LENGTH = 4_000
MAX_METADATA_LENGTH = 2_000
MAX_RESPONSE_LENGTH = 100_000


# ============================================================================
# PROVIDER
# ============================================================================


class LLMProvider:
    """
    Reusable asynchronous LLM provider.

    A persistent httpx client is used to enable connection pooling across
    multiple investigations.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        self._external_client = client is not None
        self._client = client

        self.api_key = self._get_api_key()
        self.base_url = self._get_base_url()
        self.model = self.settings.llm_model.strip()

        self._validate_configuration()

        if self._client is None:
            self._client = self._create_http_client()

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def _get_api_key(self) -> str | None:
        """
        Extract SecretStr safely without ever logging the secret.
        """

        api_key = self.settings.llm_api_key

        if api_key is None:
            return None

        try:
            value = api_key.get_secret_value()
        except AttributeError:
            value = str(api_key)

        value = value.strip()

        return value or None

    def _get_base_url(self) -> str:
        """
        Resolve the provider endpoint.
        """

        configured_url = self.settings.llm_base_url

        if configured_url:
            return configured_url.rstrip("/")

        if self.settings.llm_provider.lower() == "ollama":
            return DEFAULT_OLLAMA_BASE_URL

        return DEFAULT_OPENAI_BASE_URL

    def _validate_configuration(self) -> None:
        """
        Validate required provider configuration.
        """

        if self.settings.demo_mode:
            return

        if not self.model:
            raise LLMConfigurationError(
                "LLM_MODEL cannot be empty."
            )

        if not self.base_url:
            raise LLMConfigurationError(
                "LLM_BASE_URL cannot be empty."
            )

        if self.settings.llm_provider.lower() != "ollama":
            if not self.api_key:
                raise LLMConfigurationError(
                    "LLM_API_KEY is required when demo mode is disabled."
                )

    def _create_http_client(self) -> httpx.AsyncClient:
        """
        Create reusable async HTTP client.
        """

        timeout = httpx.Timeout(
            timeout=self.settings.llm_timeout_seconds,
            connect=self.settings.http_connect_timeout_seconds,
        )

        limits = httpx.Limits(
            max_connections=self.settings.http_max_connections,
            max_keepalive_connections=(
                self.settings.http_max_keepalive_connections
            ),
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": (
                f"{self.settings.app_name}/"
                f"{self.settings.version}"
            ),
        }

        if self.api_key:
            headers["Authorization"] = (
                f"Bearer {self.api_key}"
            )

        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            headers=headers,
        )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def aclose(self) -> None:
        """
        Close internally-created HTTP client.
        """

        if (
            self._client is not None
            and not self._external_client
        ):
            await self._client.aclose()

            self._client = None

    async def __aenter__(self) -> "LLMProvider":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def analyze(
        self,
        query: str,
        evidence: Sequence[Evidence],
        timeline: Sequence[TimelineEvent],
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze an investigation using the configured LLM.
        """

        clean_query = self._normalize_query(query)

        safe_context = self._normalize_context(
            context or {},
        )

        bounded_evidence = self._bound_evidence(
            evidence,
        )

        bounded_timeline = self._bound_timeline(
            timeline,
        )

        logger.info(
            "llm_analysis_started",
            provider=self.settings.llm_provider,
            model=self.model,
            demo_mode=self.settings.demo_mode,
            evidence_count=len(bounded_evidence),
            timeline_count=len(bounded_timeline),
        )

        # --------------------------------------------------------------------
        # DEMO MODE
        # --------------------------------------------------------------------

        if self.settings.demo_mode:
            response = self._demo_response(
                clean_query,
                bounded_evidence,
            )

            logger.info(
                "llm_demo_analysis_completed",
            )

            return response

        # --------------------------------------------------------------------
        # BUILD PROMPT
        # --------------------------------------------------------------------

        user_prompt = self._build_user_prompt(
            query=clean_query,
            evidence=bounded_evidence,
            timeline=bounded_timeline,
            context=safe_context,
        )

        # --------------------------------------------------------------------
        # CALL PROVIDER
        # --------------------------------------------------------------------

        try:
            response = await self._call_with_retries(
                user_prompt=user_prompt,
            )

            logger.info(
                "llm_analysis_completed",
                provider=self.settings.llm_provider,
                model=self.model,
            )

            return response

        except LLMError as exc:
            logger.error(
                "llm_analysis_failed",
                provider=self.settings.llm_provider,
                model=self.model,
                error_type=type(exc).__name__,
            )

            return self._fallback_response()

        except Exception:
            logger.exception(
                "llm_unexpected_failure",
                provider=self.settings.llm_provider,
            )

            return self._fallback_response()

    # ========================================================================
    # PROMPT
    # ========================================================================

    def _build_user_prompt(
        self,
        *,
        query: str,
        evidence: Sequence[Evidence],
        timeline: Sequence[TimelineEvent],
        context: Mapping[str, Any],
    ) -> str:
        """
        Build a bounded machine-readable investigation prompt.
        """

        evidence_data = [
            self._serialize_evidence(item)
            for item in evidence
        ]

        timeline_data = [
            self._serialize_timeline(item)
            for item in timeline
        ]

        context_text = self._safe_json_dumps(
            context,
            max_length=MAX_CONTEXT_LENGTH,
        )

        timeline_text = self._safe_json_dumps(
            timeline_data,
            max_length=MAX_CONTEXT_LENGTH,
        )

        evidence_text = self._safe_json_dumps(
            evidence_data,
            max_length=(
                MAX_EVIDENCE_ITEMS
                * MAX_EVIDENCE_CONTENT_LENGTH
            ),
        )

        return (
            "TRACEIQ INCIDENT INVESTIGATION\n"
            "================================\n\n"
            "INVESTIGATION QUERY\n"
            "-------------------\n"
            f"{query}\n\n"
            "CONTEXT\n"
            "-------\n"
            f"{context_text}\n\n"
            "TIMELINE\n"
            "--------\n"
            f"{timeline_text}\n\n"
            "EVIDENCE\n"
            "--------\n"
            f"{evidence_text}\n\n"
            "STRICT ANALYSIS RULES\n"
            "---------------------\n"
            "1. Analyze only the supplied evidence.\n"
            "2. Never invent commits, logs, metrics, deployments, "
            "incidents, timestamps, services, or external facts.\n"
            "3. Every root-cause hypothesis must reference valid "
            "supporting evidence IDs.\n"
            "4. Every recommendation must reference supporting "
            "evidence IDs when applicable.\n"
            "5. Clearly distinguish observed facts from hypotheses.\n"
            "6. If evidence is insufficient, explicitly state that.\n"
            "7. Return JSON only according to the required schema."
        )

    @staticmethod
    def _serialize_evidence(
        evidence: Evidence,
    ) -> dict[str, Any]:
        """
        Serialize bounded evidence.
        """

        metadata = LLMProvider._truncate_json_value(
            dict(evidence.metadata or {}),
            MAX_METADATA_LENGTH,
        )

        content = (
            evidence.content[:MAX_EVIDENCE_CONTENT_LENGTH]
            if evidence.content
            else ""
        )

        return {
            "id": evidence.id,
            "source": evidence.source,
            "title": evidence.title,
            "content": content,
            "timestamp": (
                evidence.timestamp.isoformat()
                if evidence.timestamp
                else None
            ),
            "relevance_score": evidence.relevance_score,
            "evidence_type": evidence.evidence_type,
            "metadata": metadata,
        }

    @staticmethod
    def _serialize_timeline(
        event: TimelineEvent,
    ) -> dict[str, Any]:
        """
        Serialize timeline event.
        """

        return {
            "timestamp": event.timestamp.isoformat(),
            "description": event.description,
            "evidence_ids": list(
                event.evidence_ids,
            ),
        }

    # ========================================================================
    # PROVIDER REQUEST
    # ========================================================================

    async def _call_with_retries(
        self,
        *,
        user_prompt: str,
    ) -> dict[str, Any]:
        """
        Execute provider request with bounded exponential backoff.
        """

        max_retries = max(
            0,
            int(
                self.settings.llm_max_retries,
            ),
        )

        for attempt in range(
            max_retries + 1,
        ):
            try:
                return await self._call_provider(
                    user_prompt=user_prompt,
                )

            except (
                LLMAuthenticationError,
                LLMConfigurationError,
                LLMResponseError,
            ):
                raise

            except (
                LLMRateLimitError,
                LLMTimeoutError,
                LLMError,
            ):
                if attempt >= max_retries:
                    raise

                delay = self._retry_delay(
                    attempt,
                )

                logger.warning(
                    "llm_retry_scheduled",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=round(
                        delay,
                        2,
                    ),
                )

                await asyncio.sleep(
                    delay,
                )

        raise LLMError(
            "LLM retry loop terminated unexpectedly."
        )

    async def _call_provider(
        self,
        *,
        user_prompt: str,
    ) -> dict[str, Any]:
        """
        Execute a single OpenAI-compatible chat completion request.
        """

        if self._client is None:
            raise LLMConfigurationError(
                "LLM HTTP client is not initialized."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": INVESTIGATION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
            "response_format": {
                "type": "json_object",
            },
        }

        try:
            response = await self._client.post(
                "/chat/completions",
                json=payload,
            )

        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                "LLM provider request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise LLMError(
                "LLM provider request failed."
            ) from exc

        # --------------------------------------------------------------------
        # HTTP STATUS
        # --------------------------------------------------------------------

        if response.status_code in {
            401,
            403,
        }:
            raise LLMAuthenticationError(
                "LLM provider authentication failed."
            )

        if response.status_code == 429:
            raise LLMRateLimitError(
                "LLM provider rate limit exceeded."
            )

        if response.status_code >= 500:
            raise LLMError(
                f"LLM provider server error: "
                f"HTTP {response.status_code}."
            )

        if response.status_code >= 400:
            raise LLMResponseError(
                f"LLM provider rejected the request: "
                f"HTTP {response.status_code}."
            )

        # --------------------------------------------------------------------
        # RESPONSE JSON
        # --------------------------------------------------------------------

        try:
            data = response.json()

        except ValueError as exc:
            raise LLMResponseError(
                "LLM provider returned invalid JSON."
            ) from exc

        content = self._extract_content(
            data,
        )

        return self._parse_structured_response(
            content,
        )

    # ========================================================================
    # RESPONSE PARSING
    # ========================================================================

    @staticmethod
    def _extract_content(
        data: Any,
    ) -> str:
        """
        Extract assistant message content from an OpenAI-compatible response.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise LLMResponseError(
                "LLM response must be a JSON object."
            )

        choices = data.get(
            "choices",
        )

        if not isinstance(
            choices,
            list,
        ) or not choices:
            raise LLMResponseError(
                "LLM response contains no choices."
            )

        choice = choices[0]

        if not isinstance(
            choice,
            Mapping,
        ):
            raise LLMResponseError(
                "LLM response choice has invalid format."
            )

        message = choice.get(
            "message",
        )

        if not isinstance(
            message,
            Mapping,
        ):
            raise LLMResponseError(
                "LLM response message is missing."
            )

        content = message.get(
            "content",
        )

        if not isinstance(
            content,
            str,
        ):
            raise LLMResponseError(
                "LLM response content is not text."
            )

        content = content.strip()

        if not content:
            raise LLMResponseError(
                "LLM returned empty content."
            )

        if len(content) > MAX_RESPONSE_LENGTH:
            raise LLMResponseError(
                "LLM response exceeds the safety limit."
            )

        return content

    @staticmethod
    def _parse_structured_response(
        content: str,
    ) -> dict[str, Any]:
        """
        Parse model JSON response.

        Defensively handles markdown JSON fences.
        """

        cleaned = content.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(
                lines,
            ).strip()

        try:
            parsed = json.loads(
                cleaned,
            )

        except json.JSONDecodeError as exc:
            raise LLMResponseError(
                "LLM returned malformed structured JSON."
            ) from exc

        if not isinstance(
            parsed,
            dict,
        ):
            raise LLMResponseError(
                "LLM structured response must be a JSON object."
            )

        return parsed

    # ========================================================================
    # FALLBACK
    # ========================================================================

    @staticmethod
    def _fallback_response() -> dict[str, Any]:
        """
        Safe response when the LLM is unavailable.
        """

        return {
            "summary": (
                "LLM analysis is currently unavailable. "
                "The available evidence could not be analyzed "
                "by the reasoning model."
            ),
            "likely_causes": [],
            "recommendations": [],
            "follow_up_questions": [
                (
                    "Would you like to retry the investigation "
                    "when the reasoning provider is available?"
                ),
            ],
        }

    # ========================================================================
    # DEMO MODE
    # ========================================================================

    @staticmethod
    def _demo_response(
        query: str,
        evidence: Sequence[Evidence],
    ) -> dict[str, Any]:
        """
        Deterministic demo reasoning based exclusively on supplied evidence.
        """

        normalized_query = query.casefold()

        auth_evidence = [
            item
            for item in evidence
            if (
                "auth" in item.title.casefold()
                or "401" in item.title.casefold()
                or "authentication"
                in item.content.casefold()
            )
        ]

        evidence_ids = [
            item.id
            for item in auth_evidence
        ]

        if auth_evidence:
            summary = (
                "Based on the supplied evidence, the recent "
                "authentication-related change is the strongest "
                "candidate for the observed authentication failures."
            )

            cause = (
                "Authentication middleware update caused an "
                "audience mismatch."
            )

            explanation = (
                "The supplied evidence contains authentication-related "
                "signals associated with the incident. This correlation "
                "supports the hypothesis, but deployment and client-level "
                "evidence should be checked before taking corrective action."
            )

            recommendations = [
                {
                    "action": (
                        "Compare the authentication change against "
                        "the affected client audience configuration "
                        "before deciding whether to roll it back."
                    ),
                    "reason": (
                        "This directly tests the strongest "
                        "evidence-supported hypothesis."
                    ),
                    "priority": "high",
                    "supporting_evidence_ids": evidence_ids,
                },
            ]

            confidence = "high"

        else:
            summary = (
                "The available evidence does not provide enough "
                "supporting information to establish a reliable root cause."
            )

            cause = (
                "No sufficiently supported root cause was identified "
                "from the available evidence."
            )

            explanation = (
                "No strong correlated authentication, deployment, "
                "monitoring, or other incident signal was found."
            )

            recommendations = []
            confidence = "low"

        follow_up_questions = [
            "Which service and deployment window are associated with the incident?",
            "Which monitoring signals changed immediately before the failure?",
        ]

        if (
            "auth" in normalized_query
            or "401" in normalized_query
        ):
            follow_up_questions.insert(
                0,
                "Which clients are currently failing authentication?",
            )

        return {
            "summary": summary,
            "likely_causes": [
                {
                    "cause": cause,
                    "explanation": explanation,
                    "supporting_evidence_ids": evidence_ids,
                    "confidence": confidence,
                },
            ],
            "recommendations": recommendations,
            "follow_up_questions": follow_up_questions,
        }

    # ========================================================================
    # BOUNDING / SAFETY
    # ========================================================================

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        """
        Normalize and bound investigation query.
        """

        if not isinstance(
            query,
            str,
        ):
            raise ValueError(
                "Investigation query must be a string."
            )

        normalized = query.strip()

        if not normalized:
            raise ValueError(
                "Investigation query cannot be empty."
            )

        return normalized[:MAX_QUERY_LENGTH]

    @staticmethod
    def _normalize_context(
        context: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Convert arbitrary context into bounded JSON-safe data.
        """

        result: dict[str, Any] = {}

        for key, value in context.items():
            if len(result) >= 50:
                break

            normalized_key = str(
                key,
            ).strip()

            if not normalized_key:
                continue

            result[normalized_key] = (
                LLMProvider._truncate_json_value(
                    value,
                    2_000,
                )
            )

        return result

    @staticmethod
    def _bound_evidence(
        evidence: Sequence[Evidence],
    ) -> list[Evidence]:
        """
        Preserve upstream ranking while enforcing a hard evidence limit.
        """

        return list(
            evidence[:MAX_EVIDENCE_ITEMS]
        )

    @staticmethod
    def _bound_timeline(
        timeline: Sequence[TimelineEvent],
    ) -> list[TimelineEvent]:
        """
        Enforce a hard timeline limit.
        """

        return list(
            timeline[:MAX_TIMELINE_ITEMS]
        )

    @staticmethod
    def _truncate_json_value(
        value: Any,
        max_length: int,
    ) -> Any:
        """
        Keep metadata JSON-safe and bounded.
        """

        try:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        except (
            TypeError,
            ValueError,
        ):
            return str(value)[:max_length]

        if len(encoded) <= max_length:
            return value

        return (
            encoded[:max_length]
            + "...[truncated]"
        )

    @staticmethod
    def _safe_json_dumps(
        value: Any,
        *,
        max_length: int,
    ) -> str:
        """
        Serialize data to JSON while enforcing a hard size limit.
        """

        try:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        except (
            TypeError,
            ValueError,
        ):
            encoded = json.dumps(
                str(value),
                ensure_ascii=False,
            )

        if len(encoded) > max_length:
            return (
                encoded[:max_length]
                + "\n...[context truncated]"
            )

        return encoded

    # ========================================================================
    # RETRY
    # ========================================================================

    @staticmethod
    def _retry_delay(
        attempt: int,
    ) -> float:
        """
        Exponential backoff with jitter.
        """

        base_delay = min(
            0.5 * (2**attempt),
            8.0,
        )

        jitter = random.uniform(
            0.0,
            0.25,
        )

        return base_delay + jitter


__all__ = [
    "LLMProvider",
    "LLMError",
    "LLMConfigurationError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMResponseError",
]