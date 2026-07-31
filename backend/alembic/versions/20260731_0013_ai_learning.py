"""Add ai_learning table for per-company OCR product mappings."""

from alembic import op
import sqlalchemy as sa

revision = "20260731_0013"
down_revision = "20260730_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_learning",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("ocr_text", sa.String(length=500), nullable=False),
        sa.Column("normalized_text", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("last_used", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_ai_learning_company_id_companies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_ai_learning_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning")),
        sa.UniqueConstraint("company_id", "normalized_text", name="uq_ai_learning_company_normalized_text"),
    )
    op.create_index("ix_ai_learning_company_id", "ai_learning", ["company_id"], unique=False)
    op.create_index("ix_ai_learning_company_normalized_text", "ai_learning", ["company_id", "normalized_text"], unique=False)
    op.create_index("ix_ai_learning_company_product_id", "ai_learning", ["company_id", "product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_learning_company_product_id", table_name="ai_learning")
    op.drop_index("ix_ai_learning_company_normalized_text", table_name="ai_learning")
    op.drop_index("ix_ai_learning_company_id", table_name="ai_learning")
    op.drop_table("ai_learning")
