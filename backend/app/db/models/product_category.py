from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.product import Product


class ProductCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyScopedMixin):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_product_categories_company_slug"),
        Index("ix_product_categories_company_name", "company_id", "name"),
        Index("ix_product_categories_company_parent", "company_id", "parent_id"),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    parent: Mapped[ProductCategory | None] = relationship(
        "ProductCategory",
        remote_side="ProductCategory.id",
        back_populates="children",
    )
    children: Mapped[list[ProductCategory]] = relationship(
        "ProductCategory",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    products: Mapped[list[Product]] = relationship("Product", back_populates="category_rel")
