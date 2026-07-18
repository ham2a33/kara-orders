from __future__ import annotations

from decimal import Decimal
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.order_item import OrderItem
    from app.db.models.user import User


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyScopedMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("company_id", "invoice_number", name="uq_orders_company_invoice_number"),
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("discount_total >= 0", name="discount_total_non_negative"),
        CheckConstraint("tax_total >= 0", name="tax_total_non_negative"),
        CheckConstraint("total >= 0", name="total_non_negative"),
        CheckConstraint(
            "input_method in ('manual')",
            name="input_method_valid",
        ),
        CheckConstraint(
            "status in ('draft', 'confirmed', 'completed', 'cancelled')",
            name="status_valid",
        ),
        Index("ix_orders_company_created_at", "company_id", "created_at"),
        Index("ix_orders_company_status", "company_id", "status"),
        Index("ix_orders_company_invoice_number", "company_id", "invoice_number"),
    )

    invoice_number: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    input_method: Mapped[str] = mapped_column(String(16), nullable=False)
    source_file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ai_raw_response: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="draft",
        server_default=sa.text("'draft'"),
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    company: Mapped[Company] = relationship("Company", back_populates="orders")
    created_by_user: Mapped[User] = relationship("User", back_populates="created_orders")
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
