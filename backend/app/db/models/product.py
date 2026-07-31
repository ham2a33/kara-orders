from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import CompanyScopedMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.company import Company
    from app.db.models.inventory_transaction import InventoryTransaction
    from app.db.models.product_category import ProductCategory
    from app.db.models.product_image import ProductImage
    from app.db.models.product_tag import ProductTag
    from app.db.models.order_item import OrderItem


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, CompanyScopedMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("cost IS NULL OR cost >= 0", name="cost_non_negative"),
        CheckConstraint("stock_qty IS NULL OR stock_qty >= 0", name="stock_non_negative"),
        CheckConstraint("tax_rate IS NULL OR tax_rate >= 0", name="tax_rate_non_negative"),
        CheckConstraint("unit <> ''", name="unit_not_blank"),
        Index(
            "uq_products_company_sku_not_null",
            "company_id",
            "sku",
            unique=True,
            postgresql_where=sa.text("sku IS NOT NULL"),
        ),
        Index(
            "uq_products_company_barcode_not_null",
            "company_id",
            "barcode",
            unique=True,
            postgresql_where=sa.text("barcode IS NOT NULL"),
        ),
        Index("ix_products_company_manufacturer", "company_id", "manufacturer"),
        Index("ix_products_company_name", "company_id", "name"),
        Index("ix_products_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_products_company_active", "company_id", "is_active"),
        Index("ix_products_company_category", "company_id", "category_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(80), nullable=True)
    aliases: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=sa.text("'[]'::jsonb"))
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.dialects.postgresql.UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    unit: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pcs",
        server_default=sa.text("'pcs'"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="KZT",
        server_default=sa.text("'KZT'"),
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    stock_qty: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    low_stock_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        sa.Computed(
            "to_tsvector('simple', "
            "coalesce(name, '') || ' ' || coalesce(manufacturer, '') || ' ' || coalesce(sku, '') || ' ' || "
            "coalesce(barcode, '') || ' ' || coalesce(category, '') || ' ' || "
            "coalesce(unit, ''))",
            persisted=True,
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    company: Mapped[Company] = relationship("Company", back_populates="products")
    category_rel: Mapped[ProductCategory | None] = relationship("ProductCategory", back_populates="products")
    order_items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="product")
    images: Mapped[list[ProductImage]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list[InventoryTransaction]] = relationship(
        "InventoryTransaction",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[ProductTag]] = relationship(
        "ProductTag",
        secondary="product_tag_links",
        back_populates="products",
    )
