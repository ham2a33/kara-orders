"""Add store profile fields to companies."""

from alembic import op
import sqlalchemy as sa

revision = "20260730_0012"
down_revision = "20260730_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("instagram", sa.String(length=128), nullable=True))
    op.add_column("companies", sa.Column("director_name", sa.String(length=120), nullable=True))
    op.add_column("companies", sa.Column("welcome_message", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("receipt_signature", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "receipt_signature")
    op.drop_column("companies", "welcome_message")
    op.drop_column("companies", "director_name")
    op.drop_column("companies", "instagram")
