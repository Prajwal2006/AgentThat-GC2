"""Identity Service - SSO authentication, session management, and user provisioning."""
from __future__ import annotations

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class AuthenticationError(Exception):
    """Raised when authentication fails (generic error for client security)."""
    pass


class EmailConflictError(Exception):
    """Raised when a user with the same email already exists under a different provider."""
    pass


class IdentityService:
    """Manages SSO authentication, user provisioning, and session lifecycle."""

    SUPPORTED_PROVIDERS = ["saml", "oauth2", "oidc", "entra_id"]
    MIN_SESSION_TIMEOUT_MINUTES: int = 5
    MAX_SESSION_TIMEOUT_MINUTES: int = 1440  # 24 hours
    MIN_TOKEN_REFRESH_MINUTES: int = 1
    MAX_TOKEN_REFRESH_MINUTES: int = 60

    DEFAULT_SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours
    DEFAULT_TOKEN_REFRESH_MINUTES: int = 15

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self._session_timeout_minutes = self.DEFAULT_SESSION_TIMEOUT_MINUTES
        self._token_refresh_minutes = self.DEFAULT_TOKEN_REFRESH_MINUTES

    @property
    def session_timeout_minutes(self) -> int:
        """Configurable session timeout (5min-24hr)."""
        return self._session_timeout_minutes

    @session_timeout_minutes.setter
    def session_timeout_minutes(self, value: int) -> None:
        if value < self.MIN_SESSION_TIMEOUT_MINUTES:
            value = self.MIN_SESSION_TIMEOUT_MINUTES
        elif value > self.MAX_SESSION_TIMEOUT_MINUTES:
            value = self.MAX_SESSION_TIMEOUT_MINUTES
        self._session_timeout_minutes = value

    @property
    def token_refresh_minutes(self) -> int:
        """Configurable token refresh interval (1-60min)."""
        return self._token_refresh_minutes

    @token_refresh_minutes.setter
    def token_refresh_minutes(self, value: int) -> None:
        if value < self.MIN_TOKEN_REFRESH_MINUTES:
            value = self.MIN_TOKEN_REFRESH_MINUTES
        elif value > self.MAX_TOKEN_REFRESH_MINUTES:
            value = self.MAX_TOKEN_REFRESH_MINUTES
        self._token_refresh_minutes = value

    async def authenticate_sso(
        self, provider: str, token: str
    ) -> dict[str, Any]:
        """Authenticate via SSO provider (SAML, OAuth2, OIDC, Entra ID).

        Args:
            provider: Identity provider type.
            token: Provider-issued token or assertion.

        Returns:
            Session dict with session_token, user info, and expiry.

        Raises:
            AuthenticationError: On any authentication failure (generic message).
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            self._log_auth_failure(provider, "unsupported_provider", ip_address=None)
            raise AuthenticationError("Authentication failed")

        if not token or len(token) < 10:
            self._log_auth_failure(provider, "invalid_token", ip_address=None)
            raise AuthenticationError("Authentication failed")

        # Validate token with provider (placeholder)
        claims = await self._validate_provider_token(provider, token)
        if not claims:
            self._log_auth_failure(provider, "token_validation_failed", ip_address=None)
            raise AuthenticationError("Authentication failed")

        # Create or update user from claims
        user = await self.create_or_update_user(claims)

        # Issue session
        session_token = secrets.token_urlsafe(48)
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._session_timeout_minutes)

        return {
            "session_token": session_token,
            "user_id": user["id"],
            "tenant_id": str(self.tenant_id),
            "provider": provider,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "refresh_interval_minutes": self._token_refresh_minutes,
        }

    async def create_or_update_user(self, claims: dict[str, Any]) -> dict[str, Any]:
        """Create or update a user record from IdP claims/attributes.

        Args:
            claims: Identity provider attributes (email, name, roles, etc.).

        Returns:
            User record dict.

        Raises:
            EmailConflictError: If email is already associated with a different provider.
        """
        email = claims.get("email", "").lower().strip()
        if not email:
            raise AuthenticationError("Authentication failed")

        # Placeholder: check for email conflict across providers
        existing_user = await self._find_user_by_email(email)
        if existing_user and existing_user.get("provider") != claims.get("provider"):
            raise EmailConflictError(
                f"Email '{email}' is already associated with a different identity provider"
            )

        now = datetime.now(UTC)
        user_id = existing_user["id"] if existing_user else str(uuid.uuid4())

        return {
            "id": user_id,
            "tenant_id": str(self.tenant_id),
            "email": email,
            "display_name": claims.get("name", ""),
            "provider": claims.get("provider"),
            "provider_subject": claims.get("sub"),
            "roles": claims.get("roles", []),
            "last_login_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    async def validate_session(self, session_token: str) -> dict[str, Any]:
        """Validate an active session token.

        Args:
            session_token: The session token to validate.

        Returns:
            Session status dict with user_id, valid flag, and remaining TTL.

        Raises:
            AuthenticationError: If session is invalid or expired.
        """
        if not session_token or len(session_token) < 10:
            raise AuthenticationError("Authentication failed")

        # Placeholder: real implementation looks up session in store
        now = datetime.now(UTC)

        return {
            "valid": True,
            "session_token_hash": hashlib.sha256(session_token.encode()).hexdigest()[:16],
            "tenant_id": str(self.tenant_id),
            "validated_at": now.isoformat(),
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _log_auth_failure(
        self,
        provider: str,
        reason: str,
        ip_address: str | None,
    ) -> None:
        """Log authentication failure with source IP and reason.

        Does NOT expose specific failure reason to client.
        """
        # Placeholder: real implementation writes to auth failure log
        _entry = {
            "tenant_id": str(self.tenant_id),
            "provider": provider,
            "reason": reason,
            "ip_address": ip_address,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _validate_provider_token(
        self, provider: str, token: str
    ) -> dict[str, Any] | None:
        """Validate token with the identity provider.

        Placeholder: real implementation calls provider endpoint.
        """
        # Simulate successful validation
        return {
            "sub": "provider-subject-id",
            "email": "user@example.com",
            "name": "Example User",
            "provider": provider,
            "roles": ["user"],
        }

    async def _find_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up existing user by email.

        Placeholder: real implementation queries users table.
        """
        return None
