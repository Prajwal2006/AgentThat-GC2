"""Agent Generation Studio - Manual, AI, and Optimization modes."""
from __future__ import annotations

import asyncio
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

    async def generate_agent(self, description: str, mode: str = "single_agent") -> dict:
        """AI-powered agent generation from natural language (10-2000 chars).

        Modes: single_agent, multi_agent, optimization
        Returns generated agent config for review.
        Timeout: 60 seconds.
        """
        # Validate description length
        desc_len = len(description.strip())
        if desc_len < 10 or desc_len > 2000:
            raise AgentValidationError("Description must be between 10 and 2000 characters")

        # Validate mode
        valid_modes = ("single_agent", "multi_agent", "optimization")
        if mode not in valid_modes:
            raise AgentValidationError(f"Mode must be one of: {', '.join(valid_modes)}")

        # Simulate AI generation with timeout
        async def _generate_config() -> dict:
            await asyncio.sleep(0.01)  # Simulate processing

            base_config: dict[str, Any] = {
                "name": f"Generated Agent - {description[:30]}",
                "description": description.strip(),
                "mode": mode,
                "tools": [{"type": "default", "name": "general_tool"}],
                "memory": {"type": "conversation", "max_tokens": 4096},
                "governance": {
                    "max_actions_per_minute": 60,
                    "requires_approval_for": ["destructive_actions"],
                    "confidence_threshold": 0.7,
                },
                "handoff_rules": [],
                "generated_at": datetime.now(UTC).isoformat(),
            }

            if mode == "multi_agent":
                base_config["agents"] = [
                    {"role": "coordinator", "name": "Coordinator Agent"},
                    {"role": "worker", "name": "Worker Agent"},
                ]
                base_config["handoff_rules"] = [
                    {"from": "coordinator", "to": "worker", "condition": "task_delegated"},
                ]
            elif mode == "optimization":
                base_config["optimization_targets"] = [
                    "latency",
                    "token_usage",
                    "accuracy",
                ]

            return base_config

        try:
            config = await asyncio.wait_for(_generate_config(), timeout=60.0)
        except asyncio.TimeoutError:
            raise AgentValidationError("Agent generation timed out after 60 seconds")

        # Audit log
        await self.audit.log(
            user_id=self.user_id,
            operation="generate",
            resource_type="agent",
            resource_id=uuid.uuid4(),
            details={"mode": mode, "description_length": desc_len},
        )

        return {
            "status": "generated",
            "config": config,
            "requires_review": True,
        }

    async def optimize_workflow(self, workflow_id: uuid.UUID) -> dict:
        """Analyze workflow for performance bottlenecks and generate recommendations.

        Returns up to 20 recommendations with category, affected_step, description, expected_impact.
        """
        # Simulate analysis
        recommendations: list[dict[str, Any]] = [
            {
                "id": str(uuid.uuid4()),
                "category": "performance",
                "affected_step": "step_1",
                "description": "Consider parallelizing independent data fetch operations",
                "expected_impact": 35.0,
            },
            {
                "id": str(uuid.uuid4()),
                "category": "redundancy",
                "affected_step": "step_2",
                "description": "Remove duplicate validation already performed in step_1",
                "expected_impact": 10.0,
            },
            {
                "id": str(uuid.uuid4()),
                "category": "error_handling",
                "affected_step": "step_3",
                "description": "Add retry logic for external API calls",
                "expected_impact": 20.0,
            },
            {
                "id": str(uuid.uuid4()),
                "category": "config",
                "affected_step": "step_4",
                "description": "Increase timeout for long-running model inference step",
                "expected_impact": 15.0,
            },
        ]

        # Cap at 20
        recommendations = recommendations[:20]

        await self.audit.log(
            user_id=self.user_id,
            operation="optimize_analyze",
            resource_type="workflow",
            resource_id=workflow_id,
            details={"recommendation_count": len(recommendations)},
        )

        return {
            "workflow_id": str(workflow_id),
            "recommendations": recommendations,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    async def apply_optimizations(self, workflow_id: uuid.UUID, accepted_ids: list[str]) -> dict:
        """Apply accepted optimization recommendations as new workflow version."""
        # In a real implementation, this would fetch the workflow, apply changes,
        # and create a new version while preserving the previous one.
        new_version_number = 2  # Placeholder; would increment from current

        await self.audit.log(
            user_id=self.user_id,
            operation="optimize_apply",
            resource_type="workflow",
            resource_id=workflow_id,
            details={
                "accepted_recommendations": accepted_ids,
                "new_version": new_version_number,
            },
        )

        return {
            "workflow_id": str(workflow_id),
            "previous_version": new_version_number - 1,
            "new_version": new_version_number,
            "applied_optimizations": accepted_ids,
            "applied_at": datetime.now(UTC).isoformat(),
        }
