"""Add product manufacturer for AI product selection

Revision ID: 20260722_0009_prod_mfr
Revises: 20260717_0008_saas_platform
Create Date: 2026-07-22 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260722_0009_prod_mfr"
down_revision = "20260717_0008_saas_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("manufacturer", sa.String(length=120), nullable=True))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_products_search_vector"))
    op.drop_column("products", "search_vector")
    op.add_column(
        "products",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', "
                "coalesce(name, '') || ' ' || coalesce(manufacturer, '') || ' ' || "
                "coalesce(sku, '') || ' ' || coalesce(barcode, '') || ' ' || "
                "coalesce(category, '') || ' ' || coalesce(unit, ''))",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index("ix_products_company_manufacturer", "products", ["company_id", "manufacturer"], unique=False)
    op.create_index("ix_products_search_vector", "products", ["search_vector"], unique=False, postgresql_using="gin")


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_products_search_vector"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_products_company_manufacturer"))
    op.drop_column("products", "search_vector")
    op.drop_column("products", "manufacturer")
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
    op.create_index("ix_products_search_vector", "products", ["search_vector"], unique=False, postgresql_using="gin")
