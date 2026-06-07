"""Application configuration using pydantic-settings.

Loads all environment variables with support for .env file.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── General ───────────────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://[::1]:3000"

    # ─── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentthat"

    # ─── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── Azure OpenAI ──────────────────────────────────────────────────────────
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_api_version: str = "2024-10-21"

    # ─── Session ───────────────────────────────────────────────────────────────
    session_timeout_minutes: int = 480
    token_refresh_interval_minutes: int = 15

    # ─── Azure Entra ID (SSO) ─────────────────────────────────────────────────
    azure_entra_client_id: str | None = None
    azure_entra_client_secret: str | None = None
    azure_entra_tenant_id: str | None = None

    # ─── LangFuse (Observability) ──────────────────────────────────────────────
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    # ─── Vector Store ──────────────────────────────────────────────────────────
    vector_store_type: Literal["azure_ai_search", "qdrant"] = "qdrant"
    vector_store_url: str | None = None
    vector_store_api_key: str | None = None

    # ─── Job Processing ────────────────────────────────────────────────────────
    max_job_duration_seconds: int = Field(default=1800, ge=60, le=7200)

    # ─── Helpers ───────────────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def azure_openai_configured(self) -> bool:
        """Return True if all required Azure OpenAI settings are present."""
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment_name
        )

    @property
    def azure_entra_configured(self) -> bool:
        """Return True if all required Azure Entra ID settings are present."""
        return bool(
            self.azure_entra_client_id
            and self.azure_entra_client_secret
            and self.azure_entra_tenant_id
        )


# Singleton settings instance used throughout the application
settings = Settings()
