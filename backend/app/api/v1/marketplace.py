"""Marketplace API endpoints - publishing, discovery, ratings, and asset operations."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.middleware.auth import AuthContext, get_current_user
from app.services.marketplace import (
    MarketplaceService,
    MarketplaceValidationError,
    SelfRatingError,
)

router = APIRouter(prefix="/v1/marketplace", tags=["marketplace"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class PublishListingRequest(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: str = Field(max_length=80)
    listing_type: str = Field(max_length=40)
    asset_snapshot: dict[str, Any] = Field(default_factory=dict)


class ListingResponse(BaseModel):
    id: str
    tenant_id: str
    publisher_id: str
    name: str
    description: str
    category: str
    listing_type: str
    asset_snapshot: dict[str, Any]
    status: str
    version: int
    average_rating: float | None = None
    rating_count: int = 0
    install_count: int = 0
    created_at: str
    updated_at: str


class InstallResponse(BaseModel):
    installation_id: str
    listing_id: str
    tenant_id: str
    installed_by: str
    status: str
    installed_at: str


class RateRequest(BaseModel):
    value: float = Field(ge=1.0, le=5.0)


class RatingResponse(BaseModel):
    id: str
    listing_id: str
    user_id: str
    value: float
    created_at: str


class ReviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    id: str
    listing_id: str
    user_id: str
    text: str
    created_at: str


class CloneResponse(BaseModel):
    clone_id: str
    source_listing_id: str
    tenant_id: str
    cloned_by: str
    relationship: str
    created_at: str


class ForkResponse(BaseModel):
    fork_id: str
    source_listing_id: str
    tenant_id: str
    forked_by: str
    relationship: str
    upstream_linked: bool
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ListingResponse])
async def search_listings(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    q: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=80),
    min_rating: float | None = Query(default=None, ge=1.0, le=5.0),
    listing_type: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Search marketplace listings with optional filters and pagination."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.search(
            q=q,
            category=category,
            min_rating=min_rating,
            listing_type=listing_type,
            page=page,
            page_size=page_size,
        )
    except MarketplaceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", response_model=ListingResponse, status_code=201)
async def publish_listing(
    payload: PublishListingRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Publish a new marketplace listing."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.publish(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            listing_type=payload.listing_type,
            asset_snapshot=payload.asset_snapshot,
        )
    except MarketplaceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get marketplace listing details by ID."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    # Placeholder: real implementation fetches listing from DB
    # For now reuse search with ID filter
    from app.repositories.base import NotFoundError
    try:
        results = await service.search(q=str(listing_id), page=1, page_size=1)
        if not results:
            raise HTTPException(status_code=404, detail="Listing not found")
        return results[0]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Listing not found")


@router.post("/{listing_id}/install", response_model=InstallResponse, status_code=201)
async def install_listing(
    listing_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Install a marketplace listing into the current workspace."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    return await service.install(listing_id)


@router.post("/{listing_id}/rate", response_model=RatingResponse, status_code=201)
async def rate_listing(
    listing_id: uuid.UUID,
    payload: RateRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Rate a marketplace listing (1.0-5.0 in 0.5 increments)."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.rate(listing_id, value=payload.value)
    except SelfRatingError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except MarketplaceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{listing_id}/review", response_model=ReviewResponse, status_code=201)
async def review_listing(
    listing_id: uuid.UUID,
    payload: ReviewRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Submit a text review for a marketplace listing."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    try:
        return await service.review(listing_id, text=payload.text)
    except SelfRatingError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except MarketplaceValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{listing_id}/clone", response_model=CloneResponse, status_code=201)
async def clone_listing(
    listing_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Clone a marketplace listing as an independent copy."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    return await service.clone(listing_id)


@router.post("/{listing_id}/fork", response_model=ForkResponse, status_code=201)
async def fork_listing(
    listing_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Fork a marketplace listing, maintaining lineage to the original."""
    service = MarketplaceService(db, auth.tenant_id, auth.user_id)
    return await service.fork(listing_id)
