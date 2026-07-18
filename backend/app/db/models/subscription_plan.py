from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, CheckConstraint, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company_subscription import CompanySubscription


class SubscriptionPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_subscription_plans_slug"),
        CheckConstraint("price_monthly >= 0", name="price_monthly_non_negative"),
        Index("ix_subscription_plans_is_default", "is_default"),
        Index("ix_subscription_plans_is_active", "is_active"),
    )

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KZT",
        server_default=sa.text("'KZT'"),
    )
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    setup_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=sa.text("0"),
    )
    features: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb"))
    limits: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=sa.text("'{}'::jsonb"))
    billing_cycle: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="monthly",
        server_default=sa.text("'monthly'"),
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa.text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa.text("true"))

    subscriptions: Mapped[list[CompanySubscription]] = relationship(
        "CompanySubscription",
        back_populates="plan",
    )

