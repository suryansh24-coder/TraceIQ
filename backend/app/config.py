from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    app_name: str = "TraceIQ"
    app_env: str = "development"
    debug: bool = True
    
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "traceiq_knowledge"

    # Integrations
    github_token: str = ""
    rime_api_key: str = ""
    stt_provider: str = ""
    stt_api_key: str = ""

    # Security
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # Demo Mode
    demo_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    def get_cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
