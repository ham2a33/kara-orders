"""order statuses

Revision ID: 20260722_0010_order_statuses
Revises: 20260722_0009_prod_mfr
Create Date: 2026-07-22 00:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260722_0010_order_statuses"
down_revision = "20260722_0009_prod_mfr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_valid"))
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET status = CASE
                WHEN deleted_at IS NOT NULL OR status IN ('cancelled', 'deleted') THEN 'deleted'
                WHEN status IN ('confirmed', 'completed', 'delivered') THEN 'confirmed'
                ELSE 'new'
            END
            """
        )
    )
    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(length=16),
        server_default=sa.text("'new'"),
    )
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('new', 'confirmed', 'deleted')",
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_valid"))
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET status = CASE
                WHEN status = 'deleted' THEN 'cancelled'
                WHEN status = 'confirmed' THEN 'completed'
                ELSE 'draft'
            END
            """
        )
    )
    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(length=16),
        server_default=sa.text("'draft'"),
    )
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('draft', 'confirmed', 'completed', 'cancelled')",
    )
