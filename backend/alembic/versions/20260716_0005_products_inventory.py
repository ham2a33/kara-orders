"""Add products, categories, tags, and inventory tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260716_0005_products_inventory"
down_revision = "20260716_0004_company_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_categories")),
        sa.UniqueConstraint("company_id", "slug", name="uq_product_categories_company_slug"),
    )
    op.create_index("ix_product_categories_company_name", "product_categories", ["company_id", "name"], unique=False)
    op.create_index("ix_product_categories_company_parent", "product_categories", ["company_id", "parent_id"], unique=False)
    op.create_index(op.f("ix_product_categories_deleted_at"), "product_categories", ["deleted_at"], unique=False)

    op.create_table(
        "product_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_tags")),
        sa.UniqueConstraint("company_id", "slug", name="uq_product_tags_company_slug"),
    )
    op.create_index("ix_product_tags_company_name", "product_tags", ["company_id", "name"], unique=False)
    op.create_index(op.f("ix_product_tags_deleted_at"), "product_tags", ["deleted_at"], unique=False)

    op.create_table(
        "product_tag_links",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_tags.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_images")),
    )
    op.create_index("ix_product_images_company_product", "product_images", ["company_id", "product_id"], unique=False)
    op.create_index("ix_product_images_company_created_at", "product_images", ["company_id", "created_at"], unique=False)

    op.create_table(
        "inventory_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_before", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_after", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_transactions")),
        sa.CheckConstraint(
            "transaction_type in ('stock_in', 'stock_out', 'adjustment')",
            name="transaction_type_valid",
        ),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
    )
    op.create_index(
        "ix_inventory_transactions_company_product_created_at",
        "inventory_transactions",
        ["company_id", "product_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_transactions_company_type",
        "inventory_transactions",
        ["company_id", "transaction_type"],
        unique=False,
    )

    op.drop_index("ix_products_search_vector", table_name="products")
    op.drop_column("products", "search_vector")
    op.add_column("products", sa.Column("barcode", sa.String(length=80), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("products", sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'KZT'")))
    op.add_column("products", sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True))
    op.add_column(
        "products",
        sa.Column("low_stock_threshold", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', "
                "coalesce(name, '') || ' ' || coalesce(sku, '') || ' ' || "
                "coalesce(barcode, '') || ' ' || coalesce(category, '') || ' ' || "
                "coalesce(unit, ''))",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "uq_products_company_barcode_not_null",
        "products",
        ["company_id", "barcode"],
        unique=True,
        postgresql_where=sa.text("barcode IS NOT NULL"),
    )
    op.create_index("ix_products_company_category", "products", ["company_id", "category_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inventory_transactions_company_type", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_company_product_created_at", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")

    op.drop_index("ix_product_images_company_created_at", table_name="product_images")
    op.drop_index("ix_product_images_company_product", table_name="product_images")
    op.drop_table("product_images")

    op.drop_table("product_tag_links")

    op.drop_index(op.f("ix_product_tags_deleted_at"), table_name="product_tags")
    op.drop_index("ix_product_tags_company_name", table_name="product_tags")
    op.drop_table("product_tags")

    op.drop_index(op.f("ix_product_categories_deleted_at"), table_name="product_categories")
    op.drop_index("ix_product_categories_company_parent", table_name="product_categories")
    op.drop_index("ix_product_categories_company_name", table_name="product_categories")
    op.drop_table("product_categories")

    op.drop_index("ix_products_company_category", table_name="products")
    op.drop_index("uq_products_company_barcode_not_null", table_name="products")
    op.drop_column("products", "search_vector")
    op.drop_column("products", "low_stock_threshold")
    op.drop_column("products", "tax_rate")
    op.drop_column("products", "currency")
    op.drop_column("products", "category_id")
    op.drop_column("products", "barcode")
    op.add_column(
        "products",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', "
                "coalesce(name, '') || ' ' || coalesce(sku, '') || ' ' || "
                "coalesce(category, '') || ' ' || coalesce(unit, ''))",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_products_search_vector",
        "products",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
