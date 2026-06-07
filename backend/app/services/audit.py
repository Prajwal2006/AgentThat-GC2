"""Audit logging service with append-only guarantee."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.audit import AuditLog
from app.repositories.audit_repo import AuditLogRepository


class AuditUnavailableError(Exception):
    """Raised when audit system is unavailable - blocks mutations."""
    pass


class AuditService:
    """Records immutable audit log entries for all platform operations."""
    
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = AuditLogRepository(db, tenant_id)
    
    async def log(
        self,
        *,
        user_id: uuid.UUID,
        operation: str,
        resource_type: str,
        resource_id: uuid.UUID,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Record an audit log entry. Raises if audit system unavailable."""
        try:
            entry = AuditLog(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                user_id=user_id,
                operation=operation,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                details=details,
                ip_address=ip_address,
                timestamp=datetime.now(UTC),
            )
            self.db.add(entry)
            await self.db.flush()
            return entry
        except Exception as e:
            raise AuditUnavailableError(
                "Audit logging unavailable - operation blocked"
            ) from e
    
    async def search(
        self,
        *,
        user_id: uuid.UUID | None = None,
        operation: str | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ):
        """Search audit logs with filters."""
        return await self.repo.search(
            user_id=user_id,
            operation=operation,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            offset=offset,
            limit=min(limit, 10000),
        )
