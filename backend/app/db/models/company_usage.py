from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company import Company


class CompanyUsage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_usages"
    __table_args__ = (
        sa.UniqueConstraint("company_id", name="uq_company_usages_company_id"),
        CheckConstraint("monthly_ai_requests >= 0", name="monthly_ai_requests_non_negative"),
        CheckConstraint("monthly_token_usage >= 0", name="monthly_token_usage_non_negative"),
        CheckConstraint("storage_usage_bytes >= 0", name="storage_usage_bytes_non_negative"),
        Index("ix_company_usages_period", "company_id", "period_start"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    period_end: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    monthly_ai_requests: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    monthly_token_usage: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    estimated_ai_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    recognition_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    average_recognition_time_ms: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    storage_usage_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, default=0, server_default=sa.text("0"))

    company: Mapped[Company] = relationship("Company", back_populates="usage")

