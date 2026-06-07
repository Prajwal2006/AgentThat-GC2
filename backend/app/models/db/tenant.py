from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default="standard")
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=5)
    data_residency_region: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=480)
    token_refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    hourly_cost_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("75.00")
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    audit_retention_days: Mapped[int] = mapped_column(Integer, default=365)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
