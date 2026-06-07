"""Agent Generation Studio - Manual, AI, and Optimization modes."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.agent import Agent, AgentVersion
from app.repositories.agent_repo import AgentRepository, AgentVersionRepository
from app.services.audit import AuditService


class AgentValidationError(Exception):
    """Agent configuration validation failure."""
    pass


class AgentStudioService:
    """Service for creating, generating, and optimizing agents."""
    
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = AgentRepository(db, tenant_id)
        self.version_repo = AgentVersionRepository(db, tenant_id)
        self.audit = AuditService(db, tenant_id)
    
    async def create_agent(
        self,
        *,
        name: str,
        description: str,
        category: str,
        components: list[dict[str, Any]] | None = None,
        connections: list[dict[str, Any]] | None = None,
    ) -> Agent:
        """Create agent in manual mode with validation."""
        # Validate input
        self._validate_name(name)
        self._validate_description(description)
        
        # Validate completeness if components provided
        if components:
            self._validate_completeness(components, connections or [])
        
        # Create agent
        agent = Agent(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            name=name.strip(),
            description=description.strip(),
            category=category.strip() or "General",
            lifecycle_state="draft",
            usage_count=0,
            current_version=1,
            created_by=self.user_id,
        )
        await self.repo.create(agent)
        
        # Create initial version
        version = AgentVersion(
            id=uuid.uuid4(),
            agent_id=agent.id,
            tenant_id=self.tenant_id,
            version_number=1,
            components=components or [],
            connections=connections or [],
            tools=[],
            created_by=self.user_id,
        )
        await self.version_repo.create(version)
        
        # Audit log
        await self.audit.log(
            user_id=self.user_id,
            operation="create",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": name, "category": category, "mode": "manual"},
        )
        
        return agent
    
    async def list_agents(self, *, offset: int = 0, limit: int = 50) -> Sequence[Agent]:
        """List agents for the current tenant."""
        return await self.repo.list_all(offset=offset, limit=limit)
    
    async def get_agent(self, agent_id: uuid.UUID) -> Agent:
        """Get agent by ID."""
        return await self.repo.get_by_id(agent_id)
    
    async def update_agent(
        self,
        agent_id: uuid.UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        components: list[dict[str, Any]] | None = None,
        connections: list[dict[str, Any]] | None = None,
    ) -> Agent:
        """Update agent and create new version."""
        agent = await self.repo.get_by_id(agent_id)
        
        if name:
            self._validate_name(name)
            agent.name = name.strip()
        if description:
            self._validate_description(description)
            agent.description = description.strip()
        if category:
            agent.category = category.strip()
        
        # Create new version if components changed
        if components is not None:
            agent.current_version += 1
            version = AgentVersion(
                id=uuid.uuid4(),
                agent_id=agent.id,
                tenant_id=self.tenant_id,
                version_number=agent.current_version,
                components=components,
                connections=connections or [],
                tools=[],
                created_by=self.user_id,
            )
            await self.version_repo.create(version)
        
        await self.repo.update(agent)
        
        await self.audit.log(
            user_id=self.user_id,
            operation="update",
            resource_type="agent",
            resource_id=agent.id,
            details={"version": agent.current_version},
        )
        
        return agent
    
    def _validate_name(self, name: str) -> None:
        length = len(name.strip())
        if length < 2 or length > 120:
            raise AgentValidationError("Agent name must be between 2 and 120 characters")
    
    def _validate_description(self, description: str) -> None:
        length = len(description.strip())
        if length < 4 or length > 1000:
            raise AgentValidationError("Agent description must be between 4 and 1000 characters")
    
    def _validate_completeness(self, components: list[dict], connections: list[dict]) -> None:
        """Validate minimum one prompt block and one tool with connections."""
        has_prompt = any(c.get("type") == "prompt" for c in components)
        has_tool = any(c.get("type") == "tool" for c in components)
        
        if not has_prompt:
            raise AgentValidationError("Agent configuration requires at least one prompt block")
        if not has_tool:
            raise AgentValidationError("Agent configuration requires at least one tool component")
        
        if len(components) > 50:
            raise AgentValidationError("Maximum 50 components per agent configuration")
