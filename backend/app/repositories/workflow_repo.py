"""Workflow repository with tenant-scoped data access."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select

from app.models.db.workflow import Workflow, WorkflowVersion
from app.repositories.base import TenantScopedRepository


class WorkflowRepository(TenantScopedRepository[Workflow]):
    model = Workflow

    async def list_by_status(self, status: str, *, offset: int = 0, limit: int = 50) -> Sequence[Workflow]:
        result = await self.db.execute(
            self._base_query().where(Workflow.status == status).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def update_last_run(self, workflow_id: uuid.UUID) -> None:
        from datetime import datetime, UTC
        workflow = await self.get_by_id(workflow_id)
        workflow.last_run_at = datetime.now(UTC)
        await self.db.flush()


class WorkflowVersionRepository(TenantScopedRepository[WorkflowVersion]):
    model = WorkflowVersion

    async def get_latest(self, workflow_id: uuid.UUID) -> WorkflowVersion | None:
        result = await self.db.execute(
            self._base_query()
            .where(WorkflowVersion.workflow_id == workflow_id)
            .order_by(WorkflowVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
