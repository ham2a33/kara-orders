"""Add company management fields and invitations."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260716_0004_company_management"
down_revision = "20260716_0003_auth_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("invoice_logo_url", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("website", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'UTC'"),
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "language",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'en'"),
        ),
    )
    op.add_column(
        "companies",
        sa.Column("bin_tax_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column(
            "invoice_number_format",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'{prefix}-{number:06d}'"),
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "tax_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "companies",
        sa.Column("footer_text", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("payment_information", sa.Text(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_companies_email"), "companies", ["email"], unique=False)
    op.create_check_constraint(
        op.f("ck_companies_currency_valid"),
        "companies",
        "currency ~ '^[A-Z]{3}$'",
    )
    op.create_check_constraint(
        op.f("ck_companies_tax_percentage_valid"),
        "companies",
        "tax_percentage >= 0 AND tax_percentage <= 100",
    )

    op.create_table(
        "company_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column(
            "role",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "invited_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_invitations")),
        sa.CheckConstraint(
            "role in ('admin', 'manager', 'employee')",
            name=op.f("ck_company_invitations_role_valid"),
        ),
    )
    op.create_index(
        "uq_company_invitations_company_email_pending",
        "company_invitations",
        ["company_id", "email"],
        unique=True,
    )
    op.create_index(
        "ix_company_invitations_company_created_at",
        "company_invitations",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_company_invitations_token_hash",
        "company_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_company_invitations_deleted_at"),
        "company_invitations",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_company_invitations_deleted_at"), table_name="company_invitations")
    op.drop_index("ix_company_invitations_token_hash", table_name="company_invitations")
    op.drop_index("ix_company_invitations_company_created_at", table_name="company_invitations")
    op.drop_index("uq_company_invitations_company_email_pending", table_name="company_invitations")
    op.drop_table("company_invitations")

    op.drop_constraint(op.f("ck_companies_tax_percentage_valid"), "companies", type_="check")
    op.drop_constraint(op.f("ck_companies_currency_valid"), "companies", type_="check")
    op.drop_index(op.f("ix_companies_email"), table_name="companies")
    op.drop_column("companies", "notes")
    op.drop_column("companies", "payment_information")
    op.drop_column("companies", "footer_text")
    op.drop_column("companies", "tax_percentage")
    op.drop_column("companies", "invoice_number_format")
    op.drop_column("companies", "bin_tax_id")
    op.drop_column("companies", "language")
    op.drop_column("companies", "timezone")
    op.drop_column("companies", "website")
    op.drop_column("companies", "email")
    op.drop_column("companies", "invoice_logo_url")
