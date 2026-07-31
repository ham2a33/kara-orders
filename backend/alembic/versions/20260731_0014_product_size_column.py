"""Add optional product.size column for catalog matching."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260731_0014"
down_revision = "20260731_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("size", sa.String(length=120), nullable=True))
    op.create_index("ix_products_company_size", "products", ["company_id", "size"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_products_company_size", table_name="products")
    op.drop_column("products", "size")
