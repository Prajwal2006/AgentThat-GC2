"""Unit tests for backend/app/config.py."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Test Settings class loads environment variables and defaults correctly."""

    def test_default_values(self) -> None:
        """Settings should have sensible defaults when no env vars are set."""
        from app.config import Settings

        # Create fresh instance without any env overrides
        with patch.dict(os.environ, {}, clear=True):
            s = Settings()

        assert s.environment == "development"
        assert s.database_url == "postgresql+asyncpg://postgres:postgres@localhost:5432/agentthat"
        assert s.redis_url == "redis://localhost:6379/0"
        assert s.session_timeout_minutes == 480
        assert s.token_refresh_interval_minutes == 15
        assert s.max_job_duration_seconds == 1800
        assert s.vector_store_type == "qdrant"
        assert s.secret_key == "change-me-in-production"

    def test_environment_variable_override(self) -> None:
        """Settings should pick up values from environment variables."""
        from app.config import Settings

        env = {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql+asyncpg://prod:secret@db.example.com:5432/app",
            "REDIS_URL": "redis://redis.example.com:6379/1",
            "SESSION_TIMEOUT_MINUTES": "120",
            "SECRET_KEY": "super-secret",
            "VECTOR_STORE_TYPE": "azure_ai_search",
            "MAX_JOB_DURATION_SECONDS": "3600",
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()

        assert s.environment == "production"
        assert s.database_url == "postgresql+asyncpg://prod:secret@db.example.com:5432/app"
        assert s.redis_url == "redis://redis.example.com:6379/1"
        assert s.session_timeout_minutes == 120
        assert s.secret_key == "super-secret"
        assert s.vector_store_type == "azure_ai_search"
        assert s.max_job_duration_seconds == 3600

    def test_azure_openai_configured_false_when_missing(self) -> None:
        """azure_openai_configured should be False when any required field is None."""
        from app.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            s = Settings()

        assert s.azure_openai_configured is False

    def test_azure_openai_configured_true_when_all_set(self) -> None:
        """azure_openai_configured should be True when all required fields are set."""
        from app.config import Settings

        env = {
            "AZURE_OPENAI_ENDPOINT": "https://my-resource.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key-123",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()

        assert s.azure_openai_configured is True
        assert s.azure_openai_endpoint == "https://my-resource.openai.azure.com"
        assert s.azure_openai_api_key == "test-key-123"
        assert s.azure_openai_deployment_name == "gpt-4o"
        assert s.azure_openai_api_version == "2024-10-21"

    def test_azure_entra_configured_property(self) -> None:
        """azure_entra_configured should reflect whether all Entra fields are set."""
        from app.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            s = Settings()
        assert s.azure_entra_configured is False

        env = {
            "AZURE_ENTRA_CLIENT_ID": "client-id",
            "AZURE_ENTRA_CLIENT_SECRET": "client-secret",
            "AZURE_ENTRA_TENANT_ID": "tenant-id",
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
        assert s.azure_entra_configured is True

    def test_cors_origins_list_parsing(self) -> None:
        """cors_origins_list should split comma-separated string into a list."""
        from app.config import Settings

        env = {"CORS_ORIGINS": "http://a.com, http://b.com , http://c.com"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()

        assert s.cors_origins_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_singleton_settings_importable(self) -> None:
        """The module should export a singleton settings instance."""
        from app.config import settings

        assert settings is not None
        assert hasattr(settings, "environment")
        assert hasattr(settings, "database_url")

    def test_max_job_duration_validation(self) -> None:
        """max_job_duration_seconds should enforce ge=60 and le=7200."""
        from pydantic import ValidationError

        from app.config import Settings

        with patch.dict(os.environ, {"MAX_JOB_DURATION_SECONDS": "10"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        with patch.dict(os.environ, {"MAX_JOB_DURATION_SECONDS": "9999"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()
