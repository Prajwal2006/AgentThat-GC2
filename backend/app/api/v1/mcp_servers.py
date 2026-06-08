"""MCP Server Management API endpoints - create, activate, version, and rollback."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.middleware.rbac import require_role
from app.services.mcp_manager import (
    MCPServerManager,
    MCPValidationError,
    MCPSourceError,
)

router = APIRouter(prefix="/v1/mcp-servers", tags=["mcp-servers"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class CreateMCPServerRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    source_type: str = Field(max_length=40)
    source_config: dict[str, Any] = Field(default_factory=dict)


class MCPServerResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    source_type: str
    source_config: dict[str, Any] = Field(default_factory=dict)
    status: str
    version: int
    capabilities: list[str] = Field(default_factory=list)
    created_by: str
    created_at: str
    updated_at: str | None = None


class ActivateResponse(BaseModel):
    id: str
    tenant_id: str
    status: str
    activated_at: str
    health: dict[str, Any] = Field(default_factory=dict)


class RollbackRequest(BaseModel):
    target_version: int = Field(ge=1)


class RollbackResponse(BaseModel):
    id: str
    tenant_id: str
    status: str
    version: int
    rolled_back_at: str
    rolled_back_by: str


class VersionResponse(BaseModel):
    server_id: str
    version: int
    status: str
    created_by: str
    created_at: str
    changelog: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=MCPServerResponse, status_code=201)
async def create_mcp_server(
    payload: CreateMCPServerRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create an MCP server from specification with validation. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = MCPServerManager(db, auth.tenant_id, auth.user_id)
    try:
        return await service.create_server(
            name=payload.name,
            source_type=payload.source_type,
            source_config=payload.source_config,
        )
    except MCPSourceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MCPValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=list[MCPServerResponse])
async def list_mcp_servers(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """List all MCP servers for the current tenant. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = MCPServerManager(db, auth.tenant_id, auth.user_id)
    # Placeholder: real implementation calls service.list_servers()
    return []


@router.post("/{server_id}/activate", response_model=ActivateResponse)
async def activate_mcp_server(
    server_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Validate and activate an MCP server. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = MCPServerManager(db, auth.tenant_id, auth.user_id)
    try:
        return await service.activate(server_id)
    except MCPValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{server_id}/rollback", response_model=RollbackResponse)
async def rollback_mcp_server(
    server_id: uuid.UUID,
    payload: RollbackRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Rollback an MCP server to a previous version. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = MCPServerManager(db, auth.tenant_id, auth.user_id)
    try:
        return await service.rollback(server_id, target_version=payload.target_version)
    except MCPValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{server_id}/versions", response_model=list[VersionResponse])
async def get_version_history(
    server_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve version history for an MCP server. Requires Developer+ role."""
    checker = require_role("Developer")
    checker(auth)

    service = MCPServerManager(db, auth.tenant_id, auth.user_id)
    return await service.get_versions(server_id)
