"""Audit log API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.audit import AuditService

router = APIRouter(prefix="/v1/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    operation: str
    resource_type: str
    resource_id: uuid.UUID
    outcome: str
    details: dict | None = None
    ip_address: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[AuditLogResponse])
async def search_audit_logs(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: uuid.UUID | None = Query(default=None),
    operation: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=10000),
):
    """Search audit logs (Admin only)."""
    # Enforce admin role
    admin_check = require_role("Admin")
    admin_check(auth)
    
    service = AuditService(db, auth.tenant_id)
    logs = await service.search(
        user_id=user_id,
        operation=operation,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        offset=offset,
        limit=limit,
    )
    return logs
