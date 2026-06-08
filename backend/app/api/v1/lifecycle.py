"""Agent Lifecycle API endpoints - state transitions and version history."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.agent_lifecycle import AgentLifecycleManager, InvalidStateTransition

router = APIRouter(prefix="/v1/agents", tags=["agent-lifecycle"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class TransitionRequest(BaseModel):
    target_state: str = Field(max_length=40)
    reason: str | None = Field(default=None, max_length=500)
    deprecation_message: str | None = Field(default=None, max_length=1000)


class TransitionResponse(BaseModel):
    id: str
    name: str
    lifecycle_state: str
    previous_state: str
    transitioned_by: str
    transitioned_at: str

    class Config:
        from_attributes = True


class VersionHistoryEntry(BaseModel):
    id: str
    agent_id: str
    from_state: str
    to_state: str
    actor_id: str
    reason: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/{agent_id}/transition", response_model=TransitionResponse)
async def transition_agent_state(
    agent_id: uuid.UUID,
    payload: TransitionRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Transition an agent to a new lifecycle state with validation. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = AgentLifecycleManager(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        agent = await service.transition(
            agent_id=agent_id,
            target_state=payload.target_state,
            reason=payload.reason,
            deprecation_message=payload.deprecation_message,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))

    # After transition, agent.lifecycle_state == target_state
    return TransitionResponse(
        id=str(agent.id),
        name=agent.name,
        lifecycle_state=agent.lifecycle_state,
        previous_state=payload.target_state,  # Service already applied; see transition history for full audit
        transitioned_by=str(auth.user_id),
        transitioned_at=datetime.utcnow().isoformat(),
    )


@router.get("/{agent_id}/versions", response_model=list[VersionHistoryEntry])
async def get_agent_version_history(
    agent_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get lifecycle transition history for an agent."""
    service = AgentLifecycleManager(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.get_transition_history(agent_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")
