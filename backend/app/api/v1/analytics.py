"""Analytics API endpoints - adoption metrics, department breakdown, and reporting."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.adoption import AdoptionPlatformService

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class MetricsResponse(BaseModel):
    tenant_id: str
    calculated_at: str
    adoption_rate: float
    efficiency: float
    time_saved_hours: float
    cost_reduction: float
    roi: float


class DepartmentMetricResponse(BaseModel):
    department: str | None = None
    adoption_rate: float = 0.0
    efficiency: float = 0.0
    time_saved_hours: float = 0.0
    cost_reduction: float = 0.0
    roi: float = 0.0


class GenerateReportRequest(BaseModel):
    period: str = Field(max_length=20)
    department: str | None = Field(default=None, max_length=120)


class ReportResponse(BaseModel):
    report_id: str
    tenant_id: str
    period: str
    department: str | None = None
    generated_at: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class ExportReportRequest(BaseModel):
    report_id: str = Field(max_length=100)
    format: str = Field(max_length=20)


class ExportResponse(BaseModel):
    report_id: str
    format: str
    status: str
    download_url: str | None = None
    outline: dict[str, Any] | None = None
    generated_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=MetricsResponse)
async def get_aggregate_metrics(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get aggregate adoption metrics for the current tenant. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = AdoptionPlatformService(db, auth.tenant_id)
    return await service.calculate_metrics()


@router.get("/departments", response_model=list[DepartmentMetricResponse])
async def get_department_breakdown(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get adoption metrics broken down by department. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = AdoptionPlatformService(db, auth.tenant_id)
    return await service.get_department_metrics()


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: GenerateReportRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Generate an aggregated adoption report. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = AdoptionPlatformService(db, auth.tenant_id)
    try:
        return await service.generate_report(
            period=payload.period,
            department=payload.department,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))


@router.post("/export", response_model=ExportResponse)
async def export_report(
    payload: ExportReportRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Export a generated report as PDF or presentation. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = AdoptionPlatformService(db, auth.tenant_id)
    try:
        return await service.export_report(
            report_id=payload.report_id,
            format=payload.format,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
