from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.base import Base
from app.db.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company_subscription import CompanySubscription
    from app.db.models.company_usage import CompanyUsage
    from app.db.models.notification import Notification
    from app.db.models.order import Order
    from app.db.models.company_invitation import CompanyInvitation
    from app.db.models.product import Product
    from app.db.models.user import User


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_valid"),
        CheckConstraint("tax_percentage >= 0 AND tax_percentage <= 100", name="tax_percentage_valid"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    invoice_logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
        server_default=sa.text("'UTC'"),
    )
    language: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="en",
        server_default=sa.text("'en'"),
    )
    bin_tax_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KZT",
        server_default=sa.text("'KZT'"),
    )
    invoice_prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="INV",
        server_default=sa.text("'INV'"),
    )
    next_invoice_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    invoice_number_format: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="{prefix}-{number:06d}",
        server_default=sa.text("'{prefix}-{number:06d}'"),
    )
    tax_percentage: Mapped[Decimal] = mapped_column(
        sa.Numeric(5, 2),
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    footer_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list[CompanyInvitation]] = relationship(
        "CompanyInvitation",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    subscription: Mapped[CompanySubscription | None] = relationship(
        "CompanySubscription",
        back_populates="company",
        cascade="all, delete-orphan",
        uselist=False,
    )
    usage: Mapped[CompanyUsage | None] = relationship(
        "CompanyUsage",
        back_populates="company",
        cascade="all, delete-orphan",
        uselist=False,
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="company",
        cascade="all, delete-orphan",
    )
