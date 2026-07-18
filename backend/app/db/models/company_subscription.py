from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.subscription_plan import SubscriptionPlan


class CompanySubscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_subscriptions"
    __table_args__ = (
        sa.UniqueConstraint("company_id", name="uq_company_subscriptions_company_id"),
        CheckConstraint(
            "status in ('trialing', 'active', 'past_due', 'suspended', 'expired', 'canceled', 'lifetime', 'custom')",
            name="status_valid",
        ),
        CheckConstraint("ai_requests_monthly >= 0", name="ai_requests_monthly_non_negative"),
        CheckConstraint("ai_tokens_monthly >= 0", name="ai_tokens_monthly_non_negative"),
        CheckConstraint("storage_usage_bytes >= 0", name="storage_usage_bytes_non_negative"),
        Index("ix_company_subscriptions_status", "status"),
        Index("ix_company_subscriptions_company_plan", "company_id", "plan_id"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="trialing",
        server_default=sa.text("'trialing'"),
    )
    trial_end: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    subscription_start: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    subscription_end: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    billing_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
    setup_fee_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
    setup_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    setup_fee_paid_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    period_start: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    ai_requests_monthly: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    ai_tokens_monthly: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    ai_estimated_cost_monthly: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    recognition_count_monthly: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default=sa.text("0"))
    average_recognition_time_ms: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    storage_usage_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, default=0, server_default=sa.text("0"))
    extra: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb"))

    company: Mapped[Company] = relationship("Company", back_populates="subscription")
    plan: Mapped[SubscriptionPlan] = relationship("SubscriptionPlan", back_populates="subscriptions")

