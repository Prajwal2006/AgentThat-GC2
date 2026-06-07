"""Agent Lifecycle Manager - state machine with validation and governance."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.agent import Agent, AgentStateTransition
from app.repositories.agent_repo import AgentRepository, AgentTransitionRepository
from app.services.audit import AuditService


class InvalidStateTransition(Exception):
    """Raised when an invalid lifecycle state transition is attempted."""
    def __init__(self, current_state: str, target_state: str, allowed: list[str]):
        self.current_state = current_state
        self.target_state = target_state
        self.allowed = allowed
        super().__init__(
            f"Cannot transition from '{current_state}' to '{target_state}'. "
            f"Allowed transitions: {', '.join(allowed)}"
        )


VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["testing", "retired"],
    "testing": ["staging", "retired"],
    "staging": ["production", "retired"],
    "production": ["deprecated", "retired"],
    "deprecated": ["retired"],
    "retired": [],
}


class AgentLifecycleManager:
    """Manages agent state transitions with validation and governance."""
    
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = AgentRepository(db, tenant_id)
        self.transition_repo = AgentTransitionRepository(db, tenant_id)
        self.audit = AuditService(db, tenant_id)
    
    def get_allowed_transitions(self, current_state: str) -> list[str]:
        """Get allowed target states from current state."""
        return VALID_TRANSITIONS.get(current_state, [])
    
    def validate_transition(self, current_state: str, target_state: str) -> bool:
        """Check if transition is valid per state machine rules."""
        allowed = self.get_allowed_transitions(current_state)
        return target_state in allowed
    
    async def transition(
        self,
        agent_id: uuid.UUID,
        target_state: str,
        *,
        reason: str | None = None,
        deprecation_message: str | None = None,
        replacement_agent_id: uuid.UUID | None = None,
    ) -> Agent:
        """Execute a lifecycle state transition with validation."""
        agent = await self.repo.get_by_id(agent_id)
        current_state = agent.lifecycle_state
        
        # Validate transition
        allowed = self.get_allowed_transitions(current_state)
        if target_state not in allowed:
            raise InvalidStateTransition(current_state, target_state, allowed)
        
        # Apply transition
        agent.lifecycle_state = target_state
        
        # Handle deprecated state
        if target_state == "deprecated":
            if deprecation_message:
                agent.deprecation_message = deprecation_message
            if replacement_agent_id:
                agent.replacement_agent_id = replacement_agent_id
        
        # Record transition
        transition = AgentStateTransition(
            id=uuid.uuid4(),
            agent_id=agent.id,
            tenant_id=self.tenant_id,
            from_state=current_state,
            to_state=target_state,
            actor_id=self.user_id,
            reason=reason,
        )
        await self.transition_repo.create(transition)
        await self.repo.update(agent)
        
        # Audit
        await self.audit.log(
            user_id=self.user_id,
            operation="transition",
            resource_type="agent",
            resource_id=agent.id,
            details={
                "from_state": current_state,
                "to_state": target_state,
                "reason": reason,
            },
        )
        
        return agent
    
    async def get_transition_history(self, agent_id: uuid.UUID):
        """Get transition history for an agent."""
        return await self.transition_repo.list_for_agent(agent_id)
