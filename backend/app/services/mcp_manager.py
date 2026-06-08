"""MCP Server Manager - lifecycle management with version control and validation."""
from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class MCPValidationError(Exception):
    """Raised when MCP server fails protocol compliance validation."""
    pass


class MCPSourceError(Exception):
    """Raised when MCP source is unreachable or malformed."""
    pass


class MCPServerManager:
    """Manages MCP server creation, activation, versioning, and rollback."""

    VALIDATION_TIMEOUT_SECONDS: float = 60.0
    ACTIVATION_TIMEOUT_SECONDS: float = 30.0
    ROLLBACK_TIMEOUT_SECONDS: float = 30.0

    REQUIRED_CAPABILITIES = ["tools/list", "tools/call"]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def create_server(
        self,
        name: str,
        source_type: str,
        source_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create an MCP server from specification with validation.

        Args:
            name: Human-readable server name.
            source_type: Source type (e.g. 'github', 'url', 'inline').
            source_config: Configuration for fetching the server source.

        Returns:
            Server record dict in 'draft' status.

        Raises:
            MCPSourceError: If source is unreachable or malformed.
            MCPValidationError: If spec validation fails within 60s.
        """
        server_id = uuid.uuid4()
        created_at = datetime.now(UTC)

        # Validate source accessibility
        try:
            await asyncio.wait_for(
                self._validate_source(source_type, source_config),
                timeout=self.VALIDATION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise MCPSourceError(
                f"Source validation timed out after {self.VALIDATION_TIMEOUT_SECONDS}s"
            )

        # Validate spec compliance
        try:
            compliance = await asyncio.wait_for(
                self._validate_protocol_compliance(source_config),
                timeout=self.VALIDATION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise MCPValidationError(
                f"Protocol compliance check timed out after {self.VALIDATION_TIMEOUT_SECONDS}s"
            )

        if not compliance["passed"]:
            raise MCPValidationError(
                f"Protocol compliance failure: {compliance['reason']}"
            )

        return {
            "id": str(server_id),
            "tenant_id": str(self.tenant_id),
            "name": name,
            "source_type": source_type,
            "source_config": source_config,
            "status": "draft",
            "version": 1,
            "capabilities": compliance.get("capabilities", []),
            "created_by": str(self.user_id),
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

    async def activate(self, server_id: uuid.UUID) -> dict[str, Any]:
        """Validate and activate an MCP server within 30s.

        Args:
            server_id: The server to activate.

        Returns:
            Updated server record with 'active' status.

        Raises:
            MCPValidationError: If protocol compliance check fails.
        """
        activated_at = datetime.now(UTC)

        try:
            health = await asyncio.wait_for(
                self._health_check(server_id),
                timeout=self.ACTIVATION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise MCPValidationError(
                f"Activation timed out after {self.ACTIVATION_TIMEOUT_SECONDS}s"
            )

        if not health["healthy"]:
            raise MCPValidationError(
                f"Health check failed: {health.get('reason', 'unknown')}"
            )

        return {
            "id": str(server_id),
            "tenant_id": str(self.tenant_id),
            "status": "active",
            "activated_at": activated_at.isoformat(),
            "health": health,
        }

    async def rollback(self, server_id: uuid.UUID, target_version: int) -> dict[str, Any]:
        """Rollback server to a previous version within 30s.

        Args:
            server_id: The server to rollback.
            target_version: The version number to restore.

        Returns:
            Server record at the target version.

        Raises:
            MCPValidationError: If target version is invalid or rollback fails.
        """
        if target_version < 1:
            raise MCPValidationError("Target version must be >= 1")

        try:
            result = await asyncio.wait_for(
                self._perform_rollback(server_id, target_version),
                timeout=self.ROLLBACK_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise MCPValidationError(
                f"Rollback timed out after {self.ROLLBACK_TIMEOUT_SECONDS}s"
            )

        return result

    async def get_versions(self, server_id: uuid.UUID) -> list[dict[str, Any]]:
        """Retrieve version history for an MCP server.

        Args:
            server_id: The server ID.

        Returns:
            List of version records ordered by version number descending.
        """
        # Placeholder: real implementation queries version table
        return [
            {
                "server_id": str(server_id),
                "version": 1,
                "status": "active",
                "created_by": str(self.user_id),
                "created_at": datetime.now(UTC).isoformat(),
                "changelog": "Initial version",
            }
        ]

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _validate_source(
        self, source_type: str, source_config: dict[str, Any]
    ) -> None:
        """Validate that the source is reachable and well-formed.

        Raises:
            MCPSourceError: If source is unreachable or malformed.
        """
        valid_source_types = {"github", "url", "inline", "registry"}
        if source_type not in valid_source_types:
            raise MCPSourceError(
                f"Unsupported source type '{source_type}'. "
                f"Supported: {', '.join(sorted(valid_source_types))}"
            )

        if source_type in ("github", "url") and "uri" not in source_config:
            raise MCPSourceError(f"Source config for '{source_type}' requires 'uri' field")

        if source_type == "inline" and "spec" not in source_config:
            raise MCPSourceError("Inline source requires 'spec' field in config")

    async def _validate_protocol_compliance(
        self, source_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Check MCP protocol compliance of the server spec.

        Returns:
            Dict with 'passed', 'reason', and 'capabilities' keys.
        """
        # Placeholder: real implementation parses spec and checks MCP protocol
        return {
            "passed": True,
            "reason": None,
            "capabilities": self.REQUIRED_CAPABILITIES,
        }

    async def _health_check(self, server_id: uuid.UUID) -> dict[str, Any]:
        """Perform health check on an MCP server.

        Returns:
            Dict with 'healthy' bool and optional 'reason'.
        """
        # Placeholder: real implementation pings the server
        return {"healthy": True, "latency_ms": 45}

    async def _perform_rollback(
        self, server_id: uuid.UUID, target_version: int
    ) -> dict[str, Any]:
        """Execute version rollback.

        Returns:
            Updated server record.
        """
        rolled_back_at = datetime.now(UTC)
        return {
            "id": str(server_id),
            "tenant_id": str(self.tenant_id),
            "status": "active",
            "version": target_version,
            "rolled_back_at": rolled_back_at.isoformat(),
            "rolled_back_by": str(self.user_id),
        }
