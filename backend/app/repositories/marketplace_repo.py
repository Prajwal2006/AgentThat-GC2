"""Marketplace repository with tenant-scoped data access."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, func as sa_func

from app.models.db.marketplace import MarketplaceListing, Rating, Review
from app.repositories.base import TenantScopedRepository


class MarketplaceRepository(TenantScopedRepository[MarketplaceListing]):
    model = MarketplaceListing

    async def search(
        self, *, q: str | None = None, category: str | None = None,
        listing_type: str | None = None, min_rating: float | None = None,
        offset: int = 0, limit: int = 50
    ) -> Sequence[MarketplaceListing]:
        query = self._base_query()
        if category:
            query = query.where(MarketplaceListing.category == category)
        if listing_type:
            query = query.where(MarketplaceListing.listing_type == listing_type)
        if min_rating is not None:
            query = query.where(MarketplaceListing.average_rating >= Decimal(str(min_rating)))
        # Text search is simplified here; full-text would use pg_trgm or tsvector
        if q:
            pattern = f"%{q}%"
            query = query.where(
                MarketplaceListing.name.ilike(pattern) | MarketplaceListing.description.ilike(pattern)
            )
        return (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()

    async def recalculate_rating(self, listing_id: uuid.UUID) -> None:
        """Recalculate average rating from all ratings."""
        listing = await self.get_by_id(listing_id)
        result = await self.db.execute(
            select(sa_func.avg(Rating.value), sa_func.count(Rating.id))
            .where(Rating.listing_id == listing_id)
        )
        row = result.one()
        listing.average_rating = Decimal(str(round(float(row[0] or 0), 2)))
        listing.rating_count = row[1] or 0
        await self.db.flush()


class RatingRepository(TenantScopedRepository[Rating]):
    model = Rating

    async def get_by_user_and_listing(self, user_id: uuid.UUID, listing_id: uuid.UUID) -> Rating | None:
        result = await self.db.execute(
            self._base_query()
            .where(Rating.user_id == user_id, Rating.listing_id == listing_id)
        )
        return result.scalar_one_or_none()


class ReviewRepository(TenantScopedRepository[Review]):
    model = Review

    async def get_by_user_and_listing(self, user_id: uuid.UUID, listing_id: uuid.UUID) -> Review | None:
        result = await self.db.execute(
            self._base_query()
            .where(Review.user_id == user_id, Review.listing_id == listing_id)
        )
        return result.scalar_one_or_none()
