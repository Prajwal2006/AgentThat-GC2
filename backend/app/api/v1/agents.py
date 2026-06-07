"""Agent CRUD and Generation API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.agent_studio import AgentStudioService, AgentValidationError

router = APIRouter(prefix="/v2/agents", tags=["agents"])


class CreateAgentRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=4, max_length=1000)
    category: str = Field(default="General", max_length=80)
    components: list[dict[str, Any]] | None = None
    connections: list[dict[str, Any]] | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    category: str
    lifecycle_state: str
    usage_count: int
    current_version: int
    created_by: uuid.UUID
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class GenerateAgentRequest(BaseModel):
    description: str = Field(min_length=10, max_length=2000)
    mode: str = Field(default="single_agent")  # single_agent, multi_agent, optimization


@router.post("", response_model=AgentResponse)
async def create_agent(
    payload: CreateAgentRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new agent (Manual Mode)."""
    # Require Developer role
    checker = require_role("Developer")
    checker(auth)
    
    service = AgentStudioService(db, auth.tenant_id, auth.user_id)
    try:
        agent = await service.create_agent(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            components=payload.components,
            connections=payload.connections,
        )
    except AgentValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    return agent


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List agents for the current tenant."""
    service = AgentStudioService(db, auth.tenant_id, auth.user_id)
    return await service.list_agents(offset=offset, limit=limit)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get agent details."""
    service = AgentStudioService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.get_agent(agent_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    payload: CreateAgentRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update an existing agent."""
    checker = require_role("Developer")
    checker(auth)
    
    service = AgentStudioService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.update_agent(
            agent_id,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            components=payload.components,
            connections=payload.connections,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")
    except AgentValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
