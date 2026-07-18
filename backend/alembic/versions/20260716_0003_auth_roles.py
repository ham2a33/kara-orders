"""Expand user roles for RBAC."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260716_0003_auth_roles"
down_revision = "20260716_0002_database_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'employee' WHERE role = 'staff'")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role_valid")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_ck_users_role_valid")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_ck_users_ck_users_role_valid")
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT ck_users_role_valid
        CHECK (role in ('owner', 'admin', 'manager', 'employee'))
        """
    )


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'staff' WHERE role IN ('admin', 'manager', 'employee')")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role_valid")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_ck_users_role_valid")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_ck_users_ck_users_role_valid")
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT ck_users_role_valid
        CHECK (role in ('owner', 'staff'))
        """
    )
