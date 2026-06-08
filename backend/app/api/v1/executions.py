"""Execution API endpoints - listing, details, human-in-the-loop approval, and SSE streaming."""
from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/v1/executions", tags=["executions"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class StepExecutionResponse(BaseModel):
    id: str
    execution_id: str
    step_id: str
    agent_id: str | None = None
    status: str
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error_details: dict[str, Any] | None = None
    retry_attempts: int = 0
    confidence_score: float | None = None
    cost_usd: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int = 0
    started_at: str | None = None
    completed_at: str | None = None


class ExecutionResponse(BaseModel):
    id: str
    tenant_id: str
    workflow_id: str
    version_id: str
    status: str
    current_step_index: int = 0
    total_steps: int = 0
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    total_cost_usd: float = 0.0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_latency_ms: int = 0
    error_count: int = 0
    started_at: str
    last_step_at: str | None = None
    completed_at: str | None = None
    initiated_by: str
    steps: list[StepExecutionResponse] = Field(default_factory=list)


class ApproveStepRequest(BaseModel):
    step_id: str = Field(max_length=100)
    decision: Literal["approve", "reject"] = Field(description="Approval decision for the human-in-the-loop step")


class ApproveStepResponse(BaseModel):
    execution_id: str
    step_id: str
    decision: str
    approved_by: str
    approved_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ExecutionResponse])
async def list_executions(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List execution runs for the current tenant."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    return await service.list_executions(offset=offset, limit=limit)


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get detailed execution run including step-level data."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.get_execution(execution_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execution not found")


@router.post("/{execution_id}/approve", response_model=ApproveStepResponse)
async def approve_step(
    execution_id: uuid.UUID,
    payload: ApproveStepRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Approve or reject a human-in-the-loop step in an execution."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        return await service.approve_step(
            execution_id=execution_id,
            step_id=payload.step_id,
            decision=payload.decision,
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execution or step not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """SSE stream of execution progress events."""
    service = OrchestratorService(db, auth.tenant_id, auth.user_id)
    from app.repositories.base import NotFoundError
    try:
        event_generator = await service.stream_execution(execution_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Execution not found")

    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
