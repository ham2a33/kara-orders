"""Allow draft order status for AI order editing flow."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260731_0015"
down_revision = "20260731_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_valid"))
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('draft', 'new', 'confirmed', 'deleted')",
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_valid"))
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET status = 'new'
            WHERE status = 'draft'
            """
        )
    )
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('new', 'confirmed', 'deleted')",
    )
