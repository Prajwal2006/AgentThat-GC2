"""Workflow lifecycle API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.orchestrator import (
    OrchestratorService,
    WorkflowValidationError,
    InvalidWorkflowCommand,
)

router = APIRouter(prefix="/v2/workflows", tags=["workflows"])


class CreateWorkflowRequest(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=8, max_length=1000)
    agents: int = Field(default=2, ge=1, le=12)
    steps: list[dict[str, Any]] | None = None
    routing_config: dict[str, Any] | None = None


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    status: str
    agent_count: int
    current_version: int
    last_run_at: datetime | None = None
    created_by: uuid.UUID
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class WorkflowControlRequest(BaseModel):
    action: Literal["run", "pause", "resume"]


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    payload: CreateWorkflowRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new workflow."""
    checker = require_role("Developer")
    checker(auth)
    
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    try:
        workflow = await service.create_workflow(
            name=payload.name,
            description=payload.description,
            agent_count=payload.agents,
            steps=payload.steps,
            routing_config=payload.routing_config,
        )
    except WorkflowValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    return workflow


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List workflows for the current tenant."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    return await service.list_workflows(offset=offset, limit=limit)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get workflow details."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.get_workflow(workflow_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/{workflow_id}/control", response_model=WorkflowResponse)
async def control_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowControlRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Execute a lifecycle command on a workflow (run/pause/resume)."""
    checker = require_role("Developer")
    checker(auth)
    
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.control_workflow(workflow_id, payload.action)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except InvalidWorkflowCommand as e:
        raise HTTPException(status_code=409, detail=str(e))
