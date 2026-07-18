from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.product import Product


product_tag_links = sa.Table(
    "product_tag_links",
    Base.metadata,
    sa.Column(
        "product_id",
        sa.dialects.postgresql.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "tag_id",
        sa.dialects.postgresql.UUID(as_uuid=True),
        sa.ForeignKey("product_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ProductTag(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyScopedMixin):
    __tablename__ = "product_tags"
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_product_tags_company_slug"),
        Index("ix_product_tags_company_name", "company_id", "name"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    products: Mapped[list[Product]] = relationship(
        "Product",
        secondary=product_tag_links,
        back_populates="tags",
    )
