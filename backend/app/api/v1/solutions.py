"""Solution Architect API endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.services.solution_architect import (
    SolutionArchitectService,
    ValidationError,
    BusinessIntentError,
)

router = APIRouter(prefix="/v1/solutions", tags=["solutions"])


class GenerateSolutionRequest(BaseModel):
    name: str = Field(default="AI Workflow", max_length=120)
    requirement: str = Field(min_length=20, max_length=8000)


class GenerateSolutionResponse(BaseModel):
    id: str
    name: str
    summary: str
    agents: list[dict]
    workflow: list[dict]
    integrations: list[str]
    governance: dict
    memory_config: dict
    rag_config: dict
    deployment_config: dict
    provider: str


@router.post("/generate", response_model=GenerateSolutionResponse)
async def generate_solution(
    payload: GenerateSolutionRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Generate a complete solution architecture from a business requirement."""
    service = SolutionArchitectService()
    
    try:
        solution = await service.generate(payload.requirement, payload.name)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except BusinessIntentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    return GenerateSolutionResponse(
        id=solution.id,
        name=solution.name,
        summary=solution.summary,
        agents=[{
            "name": a.name, "purpose": a.purpose, "system_prompt": a.system_prompt,
            "tools": a.tools, "handoff_rules": a.handoff_rules, "memory_config": a.memory_config,
        } for a in solution.agents],
        workflow=[{
            "id": s.id, "name": s.name, "agent": s.agent,
            "ordering": s.ordering, "human_approval": s.human_approval,
        } for s in solution.workflow],
        integrations=solution.integrations,
        governance=solution.governance,
        memory_config=solution.memory_config,
        rag_config=solution.rag_config,
        deployment_config=solution.deployment_config,
        provider=solution.provider,
    )
