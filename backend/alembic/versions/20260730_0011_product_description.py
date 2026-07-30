"""Add product description column.

Revision ID: 20260730_0011
Revises: 20260722_0010
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260730_0011"
down_revision = "20260722_0010_order_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "description")
