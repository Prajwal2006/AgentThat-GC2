"""Tenant-scoped base repository enforcing data isolation."""
from __future__ import annotations

import uuid
from typing import TypeVar, Generic, Type, Sequence

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.base import Base

T = TypeVar("T", bound=Base)


class NotFoundError(Exception):
    """Raised when entity not found within tenant scope."""
    def __init__(self, entity_name: str, entity_id: uuid.UUID):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} {entity_id} not found")


class TenantAccessDenied(Exception):
    """Raised when operation attempted without valid tenant context."""
    pass


class TenantScopedRepository(Generic[T]):
    """Base repository that automatically scopes all queries to a tenant."""

    model: Type[T]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        if not tenant_id:
            raise TenantAccessDenied("Tenant context required for data access")
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self) -> Select:
        """All queries automatically scoped to tenant."""
        return select(self.model).where(self.model.tenant_id == self.tenant_id)

    async def get_by_id(self, entity_id: uuid.UUID) -> T:
        """Get entity by ID within tenant scope."""
        result = await self.db.execute(
            self._base_query().where(self.model.id == entity_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            raise NotFoundError(self.model.__tablename__, entity_id)
        return entity

    async def list_all(self, *, offset: int = 0, limit: int = 50) -> Sequence[T]:
        """List entities within tenant scope with pagination."""
        result = await self.db.execute(
            self._base_query().offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """Create entity, enforcing tenant_id."""
        entity.tenant_id = self.tenant_id  # Enforce tenant
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def update(self, entity: T) -> T:
        """Update entity (must belong to tenant)."""
        if entity.tenant_id != self.tenant_id:
            raise TenantAccessDenied("Cannot modify entity from another tenant")
        await self.db.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> None:
        """Delete entity by ID within tenant scope."""
        entity = await self.get_by_id(entity_id)
        await self.db.delete(entity)
        await self.db.flush()
