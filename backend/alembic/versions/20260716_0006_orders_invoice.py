"""Add order invoice fields and invoice calculation support."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260716_0006_orders_invoice"
down_revision = "20260716_0005_products_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("customer_address", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("discount_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")))
    op.add_column("orders", sa.Column("tax_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")))
    op.drop_constraint(op.f("ck_orders_input_method_valid"), "orders", type_="check")
    op.drop_constraint(op.f("ck_orders_status_valid"), "orders", type_="check")
    op.create_check_constraint(
        op.f("ck_orders_input_method_valid"),
        "orders",
        "input_method in ('manual')",
    )
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('draft', 'confirmed', 'completed', 'cancelled')",
    )
    op.create_check_constraint(op.f("ck_orders_discount_total_non_negative"), "orders", "discount_total >= 0")
    op.create_check_constraint(op.f("ck_orders_tax_total_non_negative"), "orders", "tax_total >= 0")
    op.create_index("ix_orders_company_invoice_number", "orders", ["company_id", "invoice_number"], unique=False)

    op.add_column(
        "order_items",
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "order_items",
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
    )
    op.create_check_constraint(
        op.f("ck_order_items_discount_amount_non_negative"),
        "order_items",
        "discount_amount >= 0",
    )
    op.create_check_constraint(
        op.f("ck_order_items_tax_amount_non_negative"),
        "order_items",
        "tax_amount >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_order_items_tax_amount_non_negative"), "order_items", type_="check")
    op.drop_constraint(op.f("ck_order_items_discount_amount_non_negative"), "order_items", type_="check")
    op.drop_column("order_items", "tax_amount")
    op.drop_column("order_items", "discount_amount")

    op.drop_constraint(op.f("ck_orders_tax_total_non_negative"), "orders", type_="check")
    op.drop_constraint(op.f("ck_orders_discount_total_non_negative"), "orders", type_="check")
    op.drop_constraint(op.f("ck_orders_status_valid"), "orders", type_="check")
    op.drop_constraint(op.f("ck_orders_input_method_valid"), "orders", type_="check")
    op.create_check_constraint(
        op.f("ck_orders_status_valid"),
        "orders",
        "status in ('draft', 'confirmed', 'paid', 'cancelled')",
    )
    op.create_check_constraint(
        op.f("ck_orders_input_method_valid"),
        "orders",
        "input_method in ('photo', 'voice', 'text', 'manual')",
    )
    op.drop_column("orders", "tax_total")
    op.drop_column("orders", "discount_total")
    op.drop_column("orders", "notes")
    op.drop_column("orders", "customer_address")
