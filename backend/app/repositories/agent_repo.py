"""Agent repository with tenant-scoped data access."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select

from app.models.db.agent import Agent, AgentVersion, AgentStateTransition
from app.repositories.base import TenantScopedRepository


class AgentRepository(TenantScopedRepository[Agent]):
    model = Agent

    async def list_by_status(self, status: str, *, offset: int = 0, limit: int = 50) -> Sequence[Agent]:
        result = await self.db.execute(
            self._base_query().where(Agent.lifecycle_state == status).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def list_by_category(self, category: str, *, offset: int = 0, limit: int = 50) -> Sequence[Agent]:
        result = await self.db.execute(
            self._base_query().where(Agent.category == category).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def increment_usage(self, agent_id: uuid.UUID) -> None:
        agent = await self.get_by_id(agent_id)
        agent.usage_count += 1
        await self.db.flush()


class AgentVersionRepository(TenantScopedRepository[AgentVersion]):
    model = AgentVersion

    async def get_latest(self, agent_id: uuid.UUID) -> AgentVersion | None:
        result = await self.db.execute(
            self._base_query()
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class AgentTransitionRepository(TenantScopedRepository[AgentStateTransition]):
    model = AgentStateTransition

    async def list_for_agent(self, agent_id: uuid.UUID) -> Sequence[AgentStateTransition]:
        result = await self.db.execute(
            self._base_query()
            .where(AgentStateTransition.agent_id == agent_id)
            .order_by(AgentStateTransition.transitioned_at.desc())
        )
        return result.scalars().all()
