"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/v1/health")
def health():
    return {"status": "ok", "service": "agentthat-backend"}


@router.get("/v1/health/ready")
def readiness():
    """Readiness probe - checks downstream dependencies."""
    # TODO: Check DB and Redis connectivity
    return {"status": "ready"}
