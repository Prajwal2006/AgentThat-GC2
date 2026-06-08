"""Marketplace Service - publishing, discovery, ratings, and asset management."""
from __future__ import annotations

import uuid
import math
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class MarketplaceValidationError(Exception):
    """Raised when marketplace input validation fails."""
    pass


class SelfRatingError(Exception):
    """Raised when a user attempts to rate or review their own listing."""
    pass


class MarketplaceService:
    """Manages marketplace listings, search, ratings, reviews, and asset operations."""

    VALID_CATEGORIES = [
        "agent", "workflow", "tool", "template", "connector", "integration"
    ]
    VALID_LISTING_TYPES = ["free", "premium", "enterprise"]
    RATING_INCREMENTS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    REVIEW_MIN_LENGTH = 1
    REVIEW_MAX_LENGTH = 2000

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def publish(
        self,
        name: str,
        description: str,
        category: str,
        listing_type: str,
        asset_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Publish a new marketplace listing.

        Args:
            name: Listing display name.
            description: Listing description.
            category: Category (agent, workflow, tool, etc.).
            listing_type: Pricing tier (free, premium, enterprise).
            asset_snapshot: Frozen snapshot of the asset at publish time.

        Returns:
            Published listing record.

        Raises:
            MarketplaceValidationError: If inputs are invalid.
        """
        if not name or len(name.strip()) < 3:
            raise MarketplaceValidationError("Name must be at least 3 characters")
        if not description or len(description.strip()) < 10:
            raise MarketplaceValidationError("Description must be at least 10 characters")
        if category not in self.VALID_CATEGORIES:
            raise MarketplaceValidationError(
                f"Invalid category '{category}'. Valid: {', '.join(self.VALID_CATEGORIES)}"
            )
        if listing_type not in self.VALID_LISTING_TYPES:
            raise MarketplaceValidationError(
                f"Invalid listing_type '{listing_type}'. "
                f"Valid: {', '.join(self.VALID_LISTING_TYPES)}"
            )

        listing_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "id": str(listing_id),
            "tenant_id": str(self.tenant_id),
            "publisher_id": str(self.user_id),
            "name": name.strip(),
            "description": description.strip(),
            "category": category,
            "listing_type": listing_type,
            "asset_snapshot": asset_snapshot,
            "status": "published",
            "version": 1,
            "average_rating": None,
            "rating_count": 0,
            "install_count": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    async def search(
        self,
        q: str | None = None,
        category: str | None = None,
        min_rating: float | None = None,
        listing_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """Search marketplace listings with filters and pagination.

        Args:
            q: Free-text search query.
            category: Filter by category.
            min_rating: Minimum average rating filter.
            listing_type: Filter by listing type.
            page: Page number (1-indexed).
            page_size: Results per page (max 100).

        Returns:
            List of matching listing dicts.
        """
        if page < 1:
            page = 1
        page_size = min(max(page_size, 1), 100)

        if category and category not in self.VALID_CATEGORIES:
            raise MarketplaceValidationError(f"Invalid category filter: '{category}'")
        if min_rating is not None and (min_rating < 1.0 or min_rating > 5.0):
            raise MarketplaceValidationError("min_rating must be between 1.0 and 5.0")

        # Placeholder: real implementation queries DB with filters
        return []

    async def install(self, listing_id: uuid.UUID) -> dict[str, Any]:
        """Install a marketplace listing into the tenant's workspace.

        Args:
            listing_id: The listing to install.

        Returns:
            Installation record.
        """
        installation_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "installation_id": str(installation_id),
            "listing_id": str(listing_id),
            "tenant_id": str(self.tenant_id),
            "installed_by": str(self.user_id),
            "status": "installed",
            "installed_at": now.isoformat(),
        }

    async def rate(self, listing_id: uuid.UUID, value: float) -> dict[str, Any]:
        """Rate a marketplace listing.

        Args:
            listing_id: The listing to rate.
            value: Rating value (1.0-5.0 in 0.5 increments).

        Returns:
            Rating record.

        Raises:
            SelfRatingError: If user is rating their own listing.
            MarketplaceValidationError: If rating value is invalid.
        """
        # Check self-rating (placeholder: real impl queries listing publisher)
        publisher_id = await self._get_publisher_id(listing_id)
        if publisher_id == self.user_id:
            raise SelfRatingError("Cannot rate your own listing")

        if value not in self.RATING_INCREMENTS:
            raise MarketplaceValidationError(
                f"Rating must be 1.0-5.0 in 0.5 increments. Got: {value}"
            )

        rating_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "id": str(rating_id),
            "listing_id": str(listing_id),
            "user_id": str(self.user_id),
            "value": value,
            "created_at": now.isoformat(),
        }

    async def review(self, listing_id: uuid.UUID, text: str) -> dict[str, Any]:
        """Submit a text review for a marketplace listing.

        Args:
            listing_id: The listing to review.
            text: Review text (1-2000 characters).

        Returns:
            Review record.

        Raises:
            SelfRatingError: If user is reviewing their own listing.
            MarketplaceValidationError: If review text is invalid.
        """
        publisher_id = await self._get_publisher_id(listing_id)
        if publisher_id == self.user_id:
            raise SelfRatingError("Cannot review your own listing")

        text_len = len(text.strip())
        if text_len < self.REVIEW_MIN_LENGTH or text_len > self.REVIEW_MAX_LENGTH:
            raise MarketplaceValidationError(
                f"Review text must be {self.REVIEW_MIN_LENGTH}-{self.REVIEW_MAX_LENGTH} characters"
            )

        review_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "id": str(review_id),
            "listing_id": str(listing_id),
            "user_id": str(self.user_id),
            "text": text.strip(),
            "created_at": now.isoformat(),
        }

    async def clone(self, listing_id: uuid.UUID) -> dict[str, Any]:
        """Clone a marketplace listing into the tenant's workspace as an independent copy.

        Args:
            listing_id: The listing to clone.

        Returns:
            Clone record with new asset ID.
        """
        clone_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "clone_id": str(clone_id),
            "source_listing_id": str(listing_id),
            "tenant_id": str(self.tenant_id),
            "cloned_by": str(self.user_id),
            "relationship": "clone",
            "created_at": now.isoformat(),
        }

    async def fork(self, listing_id: uuid.UUID) -> dict[str, Any]:
        """Fork a marketplace listing, maintaining lineage to the original.

        Args:
            listing_id: The listing to fork.

        Returns:
            Fork record with lineage reference.
        """
        fork_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "fork_id": str(fork_id),
            "source_listing_id": str(listing_id),
            "tenant_id": str(self.tenant_id),
            "forked_by": str(self.user_id),
            "relationship": "fork",
            "upstream_linked": True,
            "created_at": now.isoformat(),
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_publisher_id(self, listing_id: uuid.UUID) -> uuid.UUID:
        """Fetch the publisher user ID for a listing.

        Placeholder: real implementation queries the database.
        """
        # In production, this queries the listings table
        return uuid.UUID("00000000-0000-0000-0000-000000000000")
