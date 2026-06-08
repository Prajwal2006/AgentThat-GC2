"""Data Protection Service - encryption, PII redaction, and key management."""
from __future__ import annotations

import re
import uuid
import base64
import hashlib
from datetime import datetime, UTC
from typing import Any


class KeyManagementUnavailableError(Exception):
    """Raised when encryption key management service is unavailable."""
    pass


class DataProtectionService:
    """Provides data-at-rest encryption, PII redaction, and secret access auditing."""

    # PII detection patterns
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    IP_V4_PATTERN = re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    )
    # Simple name pattern: capitalized words that look like names
    NAME_PATTERN = re.compile(
        r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
    )

    REDACTION_PLACEHOLDER = "[REDACTED]"

    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self._key_available: bool = True
        self._audit_log: list[dict[str, Any]] = []

    def encrypt_at_rest(self, data: bytes) -> bytes:
        """Encrypt data at rest using AES-256 (simulation/placeholder).

        In production, this delegates to a KMS-backed envelope encryption scheme.

        Args:
            data: Raw bytes to encrypt.

        Returns:
            Encrypted bytes (base64-encoded simulation).

        Raises:
            KeyManagementUnavailableError: If encryption keys are unavailable.
        """
        if not self._key_available:
            raise KeyManagementUnavailableError(
                "Encryption key unavailable - write operations blocked"
            )

        # Simulation: XOR with derived key + base64 encode
        # Real implementation uses AES-256-GCM via KMS
        simulated_key = hashlib.sha256(
            str(self.tenant_id).encode()
        ).digest()
        encrypted = bytes(b ^ simulated_key[i % 32] for i, b in enumerate(data))
        return base64.b64encode(encrypted)

    def decrypt_at_rest(self, encrypted: bytes) -> bytes:
        """Decrypt data encrypted with encrypt_at_rest (simulation/placeholder).

        Args:
            encrypted: Base64-encoded encrypted bytes.

        Returns:
            Original decrypted bytes.

        Raises:
            KeyManagementUnavailableError: If decryption keys are unavailable.
        """
        if not self._key_available:
            raise KeyManagementUnavailableError(
                "Decryption key unavailable - read operations blocked"
            )

        # Reverse the simulation
        simulated_key = hashlib.sha256(
            str(self.tenant_id).encode()
        ).digest()
        raw = base64.b64decode(encrypted)
        decrypted = bytes(b ^ simulated_key[i % 32] for i, b in enumerate(raw))
        return decrypted

    def redact_pii(self, text: str) -> str:
        """Redact personally identifiable information from text.

        Detects and redacts:
        - Email addresses
        - IPv4 addresses
        - Person names (capitalized word pairs)

        Args:
            text: Input text potentially containing PII.

        Returns:
            Text with PII replaced by [REDACTED] placeholders.
        """
        result = self.EMAIL_PATTERN.sub(self.REDACTION_PLACEHOLDER, text)
        result = self.IP_V4_PATTERN.sub(self.REDACTION_PLACEHOLDER, result)
        result = self.NAME_PATTERN.sub(self.REDACTION_PLACEHOLDER, result)
        return result

    def validate_key_availability(self) -> bool:
        """Check whether encryption keys are available.

        If keys are unavailable, write operations MUST be blocked.

        Returns:
            True if keys are available, False otherwise.
        """
        # Placeholder: real implementation checks KMS health
        return self._key_available

    def audit_secret_access(
        self, accessor_id: uuid.UUID, secret_id: str
    ) -> None:
        """Record an audit entry for secret/key access.

        Args:
            accessor_id: The user or service accessing the secret.
            secret_id: Identifier of the accessed secret.
        """
        now = datetime.now(UTC)
        entry = {
            "tenant_id": str(self.tenant_id),
            "accessor_id": str(accessor_id),
            "secret_id": secret_id,
            "action": "access",
            "timestamp": now.isoformat(),
        }
        self._audit_log.append(entry)
