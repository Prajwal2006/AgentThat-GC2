"""Learning Platform API endpoints - courses, enrollment, assessments, and certifications."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.learning import (
    LearningPlatformService,
    PrerequisiteIncompleteError,
    AssessmentCooldownError,
)

router = APIRouter(prefix="/v1/learning", tags=["learning"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class CourseResponse(BaseModel):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    duration_hours: float | None = None
    status: str | None = None


class EnrollRequest(BaseModel):
    course_id: uuid.UUID


class EnrollmentResponse(BaseModel):
    enrollment_id: str
    course_id: str
    user_id: str
    tenant_id: str
    status: str
    enrolled_at: str


class AssessmentRequest(BaseModel):
    course_id: uuid.UUID
    answers: list[dict[str, Any]] = Field(default_factory=list)


class CertificationDetail(BaseModel):
    certification_id: str
    course_id: str
    user_id: str
    issued_at: str
    expires_at: str


class AssessmentResponse(BaseModel):
    assessment_id: str
    course_id: str
    user_id: str
    score: float
    passing_score: float
    passed: bool
    submitted_at: str
    certification: CertificationDetail | None = None


class CertificationResponse(BaseModel):
    certification_id: str | None = None
    course_id: str | None = None
    user_id: str | None = None
    issued_at: str | None = None
    expires_at: str | None = None


class TeamProgressResponse(BaseModel):
    team_id: str
    tenant_id: str
    total_members: int
    courses_completed: int
    certifications_earned: int
    average_score: float
    members: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """List all available courses for the current tenant."""
    service = LearningPlatformService(db, auth.tenant_id, auth.user_id)
    return await service.list_courses()


@router.post("/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll_in_course(
    payload: EnrollRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Enroll the current user in a course, enforcing prerequisites."""
    service = LearningPlatformService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.enroll(course_id=payload.course_id)
    except PrerequisiteIncompleteError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/assess", response_model=AssessmentResponse, status_code=201)
async def submit_assessment(
    payload: AssessmentRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Submit a course assessment. 70% passing threshold, 24hr cooldown on retries."""
    service = LearningPlatformService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.submit_assessment(
            course_id=payload.course_id,
            answers=payload.answers,
        )
    except AssessmentCooldownError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/certifications", response_model=list[CertificationResponse])
async def get_certifications(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get certifications for the current user."""
    service = LearningPlatformService(db, auth.tenant_id, auth.user_id)
    return await service.get_certifications()


@router.get("/team-progress/{team_id}", response_model=TeamProgressResponse)
async def get_team_progress(
    team_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get aggregate learning progress for a team. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = LearningPlatformService(db, auth.tenant_id, auth.user_id)
    return await service.get_team_progress(team_id)
