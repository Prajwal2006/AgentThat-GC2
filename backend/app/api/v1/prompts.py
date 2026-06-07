"""Prompt Improvement Engine API endpoints."""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user

router = APIRouter(prefix="/v1/prompts", tags=["prompts"])


class ImprovePromptRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=6000)
    business_context: str | None = Field(default=None, max_length=2000)


class PromptImprovement(BaseModel):
    category: str
    description: str
    references_context: bool = False


class ImprovePromptResponse(BaseModel):
    original_prompt: str
    improved_prompt: str
    improvements: list[PromptImprovement]
    provider: Literal["azure_openai", "deterministic"]


def _fallback_improve(prompt: str, business_context: str | None) -> ImprovePromptResponse:
    """Deterministic fallback prompt improvement."""
    improvements = [
        PromptImprovement(
            category="specificity",
            description="Added clear objectives and measurable outcomes",
            references_context=False,
        ),
        PromptImprovement(
            category="structure",
            description="Added role definition, task boundaries, and output format",
            references_context=False,
        ),
        PromptImprovement(
            category="constraints",
            description="Added success criteria and governance constraints",
            references_context=False,
        ),
    ]
    
    context_clause = ""
    if business_context:
        context_clause = f" Business context: {business_context.strip()}."
        improvements.append(PromptImprovement(
            category="context",
            description="Incorporated provided business context into improved prompt",
            references_context=True,
        ))
    
    improved = (
        f"You are an enterprise AI assistant.{context_clause} "
        f"Task: {prompt.strip()} "
        "Requirements: Provide clear, actionable output. Include success criteria. "
        "Follow governance policies. Flag uncertainty. Cite sources when applicable."
    )
    
    return ImprovePromptResponse(
        original_prompt=prompt,
        improved_prompt=improved,
        improvements=improvements,
        provider="deterministic",
    )


@router.post("/improve", response_model=ImprovePromptResponse)
async def improve_prompt(
    payload: ImprovePromptRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Improve a prompt with AI-powered suggestions."""
    # Validate length (also validated by Pydantic, but explicit for clarity)
    if len(payload.prompt) < 3 or len(payload.prompt) > 6000:
        raise HTTPException(
            status_code=422,
            detail="Prompt must be between 3 and 6000 characters"
        )
    
    # TODO: Implement LLM-powered improvement with 10s timeout
    # For now, use deterministic fallback
    return _fallback_improve(payload.prompt, payload.business_context)
