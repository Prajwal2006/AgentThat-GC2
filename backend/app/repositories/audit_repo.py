"""Audit log repository (no tenant-scoped delete allowed)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select

from app.models.db.audit import AuditLog
from app.repositories.base import TenantScopedRepository


class AuditLogRepository(TenantScopedRepository[AuditLog]):
    model = AuditLog

    async def delete(self, entity_id: uuid.UUID) -> None:
        """Audit logs are append-only - deletion is not permitted."""
        raise PermissionError("Audit logs cannot be deleted")

    async def search(
        self, *, user_id: uuid.UUID | None = None,
        operation: str | None = None, resource_type: str | None = None,
        start_time: datetime | None = None, end_time: datetime | None = None,
        offset: int = 0, limit: int = 10000
    ) -> Sequence[AuditLog]:
        query = self._base_query()
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if operation:
            query = query.where(AuditLog.operation == operation)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if start_time:
            query = query.where(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.where(AuditLog.timestamp <= end_time)
        capped = min(limit, 10000)
        return (await self.db.execute(
            query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(capped)
        )).scalars().all()
