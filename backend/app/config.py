"""
TraceIQ - Central Application Configuration

Single source of truth for backend configuration.

Configuration priority:

    Environment variables > .env > application defaults

Sensitive values must be provided through environment variables
or .env and must never be hard-coded in production.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================================
# APPLICATION SETTINGS
# ============================================================================


class Settings(BaseSettings):
    """
    Strongly typed TraceIQ application settings.

    Pydantic Settings automatically loads values from environment variables
    and the configured .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # ========================================================================
    # APPLICATION
    # ========================================================================

    app_name: str = Field(
        default="TraceIQ",
        description="Application name",
    )

    app_env: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = Field(
        default="development",
        description="Application environment",
    )

    debug: bool = Field(
        default=True,
        description="Enable FastAPI debug mode",
    )

    version: str = Field(
        default="1.0.0",
        description="TraceIQ API version",
    )

    host: str = Field(
        default="0.0.0.0",
        description="API bind host",
    )

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API bind port",
    )

    api_prefix: str = Field(
        default="/api/v1",
        description="Base API prefix",
    )

    # ========================================================================
    # LOGGING
    # ========================================================================

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(
        default="INFO",
        description="Application log level",
    )

    log_json: bool = Field(
        default=False,
        description="Emit logs in JSON format",
    )

    # ========================================================================
    # CORS
    # ========================================================================

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
        ],
        description="Allowed CORS origins",
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )

    cors_allow_methods: list[str] = Field(
        default_factory=lambda: [
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
    )

    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
    )

    # ========================================================================
    # SECURITY
    # ========================================================================

    secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        description="Application signing/encryption secret",
    )

    trusted_hosts: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
        ],
        description="Allowed Host headers",
    )

    allowed_api_keys: list[SecretStr] = Field(
        default_factory=list,
        description="Optional API keys accepted by protected endpoints",
    )

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable API rate limiting",
    )

    rate_limit_requests: int = Field(
        default=60,
        ge=1,
        description="Maximum requests per rate-limit window",
    )

    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        description="Rate-limit window in seconds",
    )

    # ========================================================================
    # HTTP CLIENT
    # ========================================================================

    http_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
        description="Default outbound HTTP timeout",
    )

    http_connect_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        le=120,
        description="Outbound HTTP connection timeout",
    )

    http_max_connections: int = Field(
        default=100,
        ge=1,
        description="Maximum outbound HTTP connections",
    )

    http_max_keepalive_connections: int = Field(
        default=20,
        ge=1,
        description="Maximum persistent HTTP connections",
    )

    # ========================================================================
    # DATABASE - POSTGRESQL
    # ========================================================================

    database_url: str = Field(
        default="postgresql+asyncpg://traceiq:traceiq@localhost:5432/traceiq",
        description="Async PostgreSQL connection URL",
    )

    database_pool_size: int = Field(
        default=10,
        ge=1,
        description="Database connection pool size",
    )

    database_max_overflow: int = Field(
        default=20,
        ge=0,
        description="Maximum additional database connections",
    )

    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Database pool checkout timeout",
    )

    database_pool_recycle: int = Field(
        default=1800,
        ge=60,
        description="Database connection recycle time",
    )

    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy SQL logging",
    )

    # ========================================================================
    # REDIS
    # ========================================================================

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    redis_enabled: bool = Field(
        default=True,
        description="Enable Redis-backed functionality",
    )

    redis_max_connections: int = Field(
        default=50,
        ge=1,
        description="Maximum Redis connections",
    )

    redis_socket_timeout: float = Field(
        default=5.0,
        gt=0,
        description="Redis socket timeout",
    )

    # ========================================================================
    # GITHUB
    # ========================================================================

    github_token: SecretStr | None = Field(
        default=None,
        description="GitHub personal access token or GitHub App token",
    )

    github_api_url: str = Field(
        default="https://api.github.com",
        description="GitHub REST API base URL",
    )

    github_api_version: str = Field(
        default="2022-11-28",
        description="GitHub API version",
    )

    github_request_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        le=120,
    )

    github_webhook_secret: SecretStr | None = Field(
        default=None,
        description="GitHub webhook verification secret",
    )

    github_default_owner: str | None = Field(
        default=None,
        description="Default GitHub repository owner",
    )

    github_default_repo: str | None = Field(
        default=None,
        description="Default GitHub repository",
    )

    # ========================================================================
    # GITHUB ACTIONS
    # ========================================================================

    github_actions_enabled: bool = Field(
        default=True,
        description="Enable GitHub Actions integration",
    )

    github_actions_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
    )

    # ========================================================================
    # MONITORING
    # ========================================================================

    monitoring_enabled: bool = Field(
        default=False,
        description="Enable external monitoring integration",
    )

    monitoring_provider: str = Field(
        default="monitoring",
        description="Monitoring provider name",
    )

    monitoring_api_url: str | None = Field(
        default=None,
        description="Monitoring provider API base URL",
    )

    monitoring_api_key: SecretStr | None = Field(
        default=None,
        description="Monitoring provider API key",
    )

    monitoring_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        le=120,
        description="Monitoring provider timeout",
    )

    # ========================================================================
    # LLM
    # ========================================================================

    llm_provider: Literal[
        "openai",
        "gemini",
        "ollama",
        "custom",
    ] = Field(
        default="openai",
        description="Primary LLM provider",
    )

    llm_api_key: SecretStr | None = Field(
        default=None,
        description="Primary LLM API key",
    )

    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Primary LLM model",
    )

    llm_base_url: str | None = Field(
        default=None,
        description="Optional custom OpenAI-compatible API endpoint",
    )

    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM generation temperature",
    )

    llm_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=32768,
        description="Maximum LLM output tokens",
    )

    llm_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        le=600,
        description="LLM request timeout",
    )

    llm_max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum LLM request retries",
    )

    # ========================================================================
    # EMBEDDINGS
    # ========================================================================

    embedding_provider: Literal[
        "openai",
        "gemini",
        "sentence_transformers",
    ] = Field(
        default="sentence_transformers",
        description="Embedding provider",
    )

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model",
    )

    embedding_dimension: int = Field(
        default=384,
        ge=1,
        description="Embedding vector dimension",
    )

    # ========================================================================
    # RAG / QDRANT
    # ========================================================================

    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )

    qdrant_api_key: SecretStr | None = Field(
        default=None,
        description="Qdrant API key",
    )

    qdrant_collection: str = Field(
        default="traceiq_knowledge",
        description="Primary Qdrant collection",
    )

    qdrant_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        le=120,
        description="Qdrant request timeout",
    )

    rag_enabled: bool = Field(
        default=True,
        description="Enable retrieval augmented generation",
    )

    rag_top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of retrieved knowledge chunks",
    )

    rag_score_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval",
    )

    rag_chunk_size: int = Field(
        default=800,
        ge=100,
        le=10000,
        description="Knowledge chunk size",
    )

    rag_chunk_overlap: int = Field(
        default=120,
        ge=0,
        description="Chunk overlap",
    )

    # ========================================================================
    # VOICE / RIME
    # ========================================================================

    voice_enabled: bool = Field(
        default=False,
        description="Enable voice functionality",
    )

    rime_api_key: SecretStr | None = Field(
        default=None,
        description="Rime API key",
    )

    rime_api_url: str = Field(
        default="https://users.rime.ai",
        description="Rime API base URL",
    )

    rime_voice: str = Field(
        default="luna",
        description="Default Rime voice",
    )

    rime_model: str = Field(
        default="arcana",
        description="Default Rime TTS model",
    )

    rime_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
        description="Rime request timeout",
    )

    # ========================================================================
    # DEMO MODE
    # ========================================================================

    demo_mode: bool = Field(
        default=False,
        description="Enable deterministic demo mode",
    )

    demo_data_path: str = Field(
        default="../demo",
        description="Path to TraceIQ demo datasets",
    )

    demo_scenario_file: str = Field(
        default="scenario.json",
        description="Demo scenario configuration",
    )

    # ========================================================================
    # INVESTIGATION
    # ========================================================================

    investigation_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        le=900,
        description="Maximum investigation execution time",
    )

    investigation_max_steps: int = Field(
        default=12,
        ge=1,
        le=100,
        description="Maximum investigation orchestration steps",
    )

    investigation_parallelism: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Maximum parallel investigation tasks",
    )

    # ========================================================================
    # EVIDENCE
    # ========================================================================

    evidence_min_confidence: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for accepted evidence",
    )

    evidence_max_age_hours: int = Field(
        default=168,
        ge=1,
        description="Maximum age of evidence before considered stale",
    )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(
        cls,
        value: str,
    ) -> str:
        """Normalize API prefix to /path format."""

        value = value.strip()

        if not value:
            return ""

        if not value.startswith("/"):
            value = f"/{value}"

        return value.rstrip("/")

    @field_validator(
        "cors_origins",
        "trusted_hosts",
        mode="before",
    )
    @classmethod
    def parse_list_values(
        cls,
        value: object,
    ) -> object:
        """
        Support both JSON-style and comma-separated environment values.

        Examples:

            CORS_ORIGINS=["http://localhost:3000"]

        or:

            CORS_ORIGINS=http://localhost:3000,http://localhost:5173
        """

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return []

            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)

                    if isinstance(parsed, list):
                        return parsed

                except json.JSONDecodeError:
                    pass

            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        return value

    @field_validator(
        "allowed_api_keys",
        mode="before",
    )
    @classmethod
    def parse_secret_list(
        cls,
        value: object,
    ) -> object:
        """Parse comma-separated API keys."""

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return []

            return [
                SecretStr(item.strip())
                for item in value.split(",")
                if item.strip()
            ]

        return value

    @field_validator("rag_chunk_overlap")
    @classmethod
    def validate_chunk_overlap(
        cls,
        value: int,
        info,
    ) -> int:
        """Ensure chunk overlap remains smaller than chunk size."""

        chunk_size = info.data.get(
            "rag_chunk_size",
            800,
        )

        if value >= chunk_size:
            raise ValueError(
                "rag_chunk_overlap must be smaller than rag_chunk_size"
            )

        return value

    # ========================================================================
    # DERIVED PROPERTIES
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""

        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Return True when running in development."""

        return self.app_env == "development"

    @property
    def database_configured(self) -> bool:
        """Return whether a database URL is configured."""

        return bool(self.database_url)

    @property
    def github_configured(self) -> bool:
        """Return whether GitHub credentials are available."""

        return self.github_token is not None

    @property
    def llm_configured(self) -> bool:
        """
        Return whether the selected LLM provider is configured.

        Ollama can operate without an API key.
        """

        if self.llm_provider == "ollama":
            return True

        return self.llm_api_key is not None

    @property
    def voice_configured(self) -> bool:
        """Return whether Rime credentials are configured."""

        return (
            self.voice_enabled
            and self.rime_api_key is not None
        )

    @property
    def qdrant_configured(self) -> bool:
        """Return whether Qdrant configuration is available."""

        return bool(self.qdrant_url)

    @property
    def monitoring_configured(self) -> bool:
        """Return whether external monitoring is configured."""

        return (
            self.monitoring_enabled
            and bool(self.monitoring_api_url)
        )

    # ========================================================================
    # PRODUCTION SAFETY
    # ========================================================================

    def validate_production(self) -> None:
        """
        Validate settings that must be safe before production startup.
        """

        if not self.is_production:
            return

        if self.debug:
            raise ValueError(
                "DEBUG must be False in production."
            )

        if (
            self.secret_key.get_secret_value()
            == "change-me-in-production"
        ):
            raise ValueError(
                "SECRET_KEY must be changed before production deployment."
            )

        if "*" in self.cors_origins:
            raise ValueError(
                "Wildcard CORS origins are not allowed in production."
            )

        if self.rate_limit_enabled and self.rate_limit_requests <= 0:
            raise ValueError(
                "Production rate limiting must allow at least one request."
            )

        if not self.llm_configured and not self.demo_mode:
            raise ValueError(
                "An LLM provider must be configured in production "
                "unless demo mode is explicitly enabled."
            )

    # ========================================================================
    # SAFE DEBUG REPRESENTATION
    # ========================================================================

    def safe_dict(self) -> dict[str, object]:
        """
        Return configuration safe for logs/debugging.

        Secret values are always redacted.
        """

        data = self.model_dump()

        secret_fields = {
            "secret_key",
            "allowed_api_keys",
            "github_token",
            "github_webhook_secret",
            "llm_api_key",
            "qdrant_api_key",
            "rime_api_key",
            "monitoring_api_key",
        }

        for field_name in secret_fields:
            if field_name in data:
                data[field_name] = "***REDACTED***"

        return data


# ============================================================================
# SETTINGS SINGLETON
# ============================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    A single settings object is used throughout the application lifecycle.
    """

    app_settings = Settings()

    app_settings.validate_production()

    return app_settings


# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================


settings = get_settings()


__all__ = [
    "Settings",
    "get_settings",
    "settings",
]