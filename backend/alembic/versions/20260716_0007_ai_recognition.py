"""Add AI recognition history and product aliases."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260716_0007_ai_recognition"
down_revision = "20260716_0006_orders_invoice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("aliases", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_index("ix_products_aliases", "products", ["aliases"], unique=False, postgresql_using="gin")

    op.create_table(
        "ai_recognitions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_type", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'completed'")),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("recognition_time_ms", sa.Integer(), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("original_file_url", sa.String(length=1024), nullable=True),
        sa.Column("original_file_path", sa.String(length=1024), nullable=True),
        sa.Column("original_file_name", sa.String(length=255), nullable=True),
        sa.Column("original_file_mime_type", sa.String(length=128), nullable=True),
        sa.Column("raw_ai_response", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("recognized_payload", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("matched_payload", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_order_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_recognitions")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_ai_recognitions_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_recognitions_user_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_order_id"], ["orders.id"], name=op.f("fk_ai_recognitions_created_order_id_orders"), ondelete="SET NULL"),
        sa.CheckConstraint("input_type in ('photo', 'voice', 'text', 'pdf')", name=op.f("ck_ai_recognitions_input_type_valid")),
        sa.CheckConstraint("status in ('completed', 'needs_review', 'failed', 'converted')", name=op.f("ck_ai_recognitions_status_valid")),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name=op.f("ck_ai_recognitions_confidence_bounds")),
        sa.CheckConstraint("tokens_used IS NULL OR tokens_used >= 0", name=op.f("ck_ai_recognitions_tokens_used_non_negative")),
        sa.CheckConstraint(
            "recognition_time_ms IS NULL OR recognition_time_ms >= 0",
            name=op.f("ck_ai_recognitions_recognition_time_ms_non_negative"),
        ),
    )
    op.create_index(op.f("ix_ai_recognitions_company_id"), "ai_recognitions", ["company_id"], unique=False)
    op.create_index(op.f("ix_ai_recognitions_created_order_id"), "ai_recognitions", ["created_order_id"], unique=False)
    op.create_index(op.f("ix_ai_recognitions_deleted_at"), "ai_recognitions", ["deleted_at"], unique=False)
    op.create_index("ix_ai_recognitions_company_created_at", "ai_recognitions", ["company_id", "created_at"], unique=False)
    op.create_index("ix_ai_recognitions_company_status", "ai_recognitions", ["company_id", "status"], unique=False)
    op.create_index("ix_ai_recognitions_company_user_created_at", "ai_recognitions", ["company_id", "user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_recognitions_company_user_created_at", table_name="ai_recognitions")
    op.drop_index("ix_ai_recognitions_company_status", table_name="ai_recognitions")
    op.drop_index("ix_ai_recognitions_company_created_at", table_name="ai_recognitions")
    op.drop_index(op.f("ix_ai_recognitions_deleted_at"), table_name="ai_recognitions")
    op.drop_index(op.f("ix_ai_recognitions_created_order_id"), table_name="ai_recognitions")
    op.drop_index(op.f("ix_ai_recognitions_company_id"), table_name="ai_recognitions")
    op.drop_table("ai_recognitions")
    op.drop_index("ix_products_aliases", table_name="products")
    op.drop_column("products", "aliases")
