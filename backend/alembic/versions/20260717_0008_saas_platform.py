"""Add SaaS platform subscription and audit tables

Revision ID: 20260717_0008_saas_platform
Revises: 20260716_0007_ai_recognition
Create Date: 2026-07-17 00:00:00.000000
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260717_0008_saas_platform"
down_revision = "20260716_0007_ai_recognition"
branch_labels = None
depends_on = None


def _plan_id(slug: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"kara-orders-plan:{slug}"))


def _system_setting_id() -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "kara-orders-system-settings"))


def _default_free_limits() -> dict[str, int | None]:
    return {
        "maximum_users": 3,
        "maximum_products": 250,
        "maximum_ai_requests": 100,
        "maximum_storage_bytes": 1_073_741_824,
        "maximum_companies": 1,
        "maximum_orders_per_month": 250,
    }


def _default_starter_limits() -> dict[str, int | None]:
    return {
        "maximum_users": 5,
        "maximum_products": 1_000,
        "maximum_ai_requests": 500,
        "maximum_storage_bytes": 5_368_709_120,
        "maximum_companies": 1,
        "maximum_orders_per_month": 1_000,
    }


def _default_enterprise_limits() -> dict[str, int | None]:
    return {
        "maximum_users": None,
        "maximum_products": None,
        "maximum_ai_requests": None,
        "maximum_storage_bytes": None,
        "maximum_companies": None,
        "maximum_orders_per_month": None,
    }


DEFAULT_BUSINESS_LIMITS = {
    "maximum_users": 20,
    "maximum_products": None,
    "maximum_ai_requests": 1000,
    "maximum_storage_bytes": None,
    "maximum_companies": 1,
    "maximum_orders_per_month": None,
}


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_super_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'KZT'"), nullable=False),
        sa.Column("price_monthly", sa.Numeric(12, 2), nullable=False),
        sa.Column("setup_fee_amount", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("billing_cycle", sa.String(length=16), server_default=sa.text("'monthly'"), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_subscription_plans_slug"),
        sa.CheckConstraint("price_monthly >= 0", name="ck_subscription_plans_price_monthly_non_negative"),
    )

    op.create_index("ix_subscription_plans_is_default", "subscription_plans", ["is_default"])
    op.create_index("ix_subscription_plans_is_active", "subscription_plans", ["is_active"])

    op.create_table(
        "system_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ai_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("maintenance_mode", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("max_upload_size_mb", sa.Integer(), server_default=sa.text("20"), nullable=False),
        sa.Column(
            "allowed_file_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("to_jsonb(ARRAY['pdf','png','jpg','jpeg','csv','xlsx']::text[])"),
            nullable=False,
        ),
        sa.Column("default_currency", sa.String(length=3), server_default=sa.text("'KZT'"), nullable=False),
        sa.Column("default_tax", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("default_currency ~ '^[A-Z]{3}$'", name="ck_system_settings_default_currency_valid"),
        sa.CheckConstraint("default_tax >= 0 AND default_tax <= 100", name="ck_system_settings_default_tax_valid"),
        sa.CheckConstraint("max_upload_size_mb >= 0", name="ck_system_settings_max_upload_size_mb_non_negative"),
    )

    op.create_table(
        "company_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=16), server_default=sa.text("'trialing'"), nullable=False),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscription_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscription_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("billing_disabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("setup_fee_paid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("setup_fee_amount", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("setup_fee_paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ai_requests_monthly", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("ai_tokens_monthly", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("ai_estimated_cost_monthly", sa.Numeric(12, 4), server_default=sa.text("0"), nullable=False),
        sa.Column("recognition_count_monthly", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("average_recognition_time_ms", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("storage_usage_bytes", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.UniqueConstraint("company_id", name="uq_company_subscriptions_company_id"),
        sa.CheckConstraint(
            "status in ('trialing', 'active', 'past_due', 'suspended', 'expired', 'canceled', 'lifetime', 'custom')",
            name="ck_company_subscriptions_status_valid",
        ),
        sa.CheckConstraint("ai_requests_monthly >= 0", name="ck_company_subscriptions_ai_requests_monthly_non_negative"),
        sa.CheckConstraint("ai_tokens_monthly >= 0", name="ck_company_subscriptions_ai_tokens_monthly_non_negative"),
        sa.CheckConstraint("storage_usage_bytes >= 0", name="ck_company_subscriptions_storage_usage_bytes_non_negative"),
    )
    op.create_index("ix_company_subscriptions_status", "company_subscriptions", ["status"])
    op.create_index("ix_company_subscriptions_company_plan", "company_subscriptions", ["company_id", "plan_id"])

    op.create_table(
        "company_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monthly_ai_requests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("monthly_token_usage", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("estimated_ai_cost", sa.Numeric(12, 4), server_default=sa.text("0"), nullable=False),
        sa.Column("recognition_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("average_recognition_time_ms", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("storage_usage_bytes", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.UniqueConstraint("company_id", name="uq_company_usages_company_id"),
        sa.CheckConstraint("monthly_ai_requests >= 0", name="ck_company_usages_monthly_ai_requests_non_negative"),
        sa.CheckConstraint("monthly_token_usage >= 0", name="ck_company_usages_monthly_token_usage_non_negative"),
        sa.CheckConstraint("storage_usage_bytes >= 0", name="ck_company_usages_storage_usage_bytes_non_negative"),
    )
    op.create_index("ix_company_usages_period", "company_usages", ["company_id", "period_start"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_audit_logs_company_created_at", "audit_logs", ["company_id", "created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default=sa.text("'unread'"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_notifications_company_status", "notifications", ["company_id", "status"])
    op.create_index("ix_notifications_user_status", "notifications", ["user_id", "status"])
    op.create_index("ix_notifications_type", "notifications", ["notification_type"])

    bind = op.get_bind()
    plan_rows = [
        {
            "id": _plan_id("free"),
            "slug": "free",
            "name": "Free",
            "description": "Entry plan for small teams getting started with Kara Orders.",
            "currency": "KZT",
            "price_monthly": 0,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": False},
            "limits": _default_free_limits(),
            "billing_cycle": "monthly",
            "is_default": False,
            "is_active": True,
        },
        {
            "id": _plan_id("starter"),
            "slug": "starter",
            "name": "Starter",
            "description": "Lightweight paid plan for growing teams.",
            "currency": "KZT",
            "price_monthly": 12000,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": True},
            "limits": _default_starter_limits(),
            "billing_cycle": "monthly",
            "is_default": False,
            "is_active": True,
        },
        {
            "id": _plan_id("business"),
            "slug": "business",
            "name": "Business",
            "description": "Default production plan with generous AI usage and unlimited growth paths.",
            "currency": "KZT",
            "price_monthly": 30000,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": True},
            "limits": DEFAULT_BUSINESS_LIMITS,
            "billing_cycle": "monthly",
            "is_default": True,
            "is_active": True,
        },
        {
            "id": _plan_id("enterprise"),
            "slug": "enterprise",
            "name": "Enterprise",
            "description": "Advanced plan for larger organizations.",
            "currency": "KZT",
            "price_monthly": 90000,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": True, "sso": True},
            "limits": _default_enterprise_limits(),
            "billing_cycle": "monthly",
            "is_default": False,
            "is_active": True,
        },
        {
            "id": _plan_id("custom"),
            "slug": "custom",
            "name": "Custom",
            "description": "Manually tailored plan for special contracts.",
            "currency": "KZT",
            "price_monthly": 0,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": True},
            "limits": _default_enterprise_limits(),
            "billing_cycle": "monthly",
            "is_default": False,
            "is_active": True,
        },
        {
            "id": _plan_id("lifetime"),
            "slug": "lifetime",
            "name": "Lifetime",
            "description": "One-time access for long-term customers.",
            "currency": "KZT",
            "price_monthly": 0,
            "setup_fee_amount": 0,
            "features": {"analytics": True, "pdf_invoices": True, "ai_recognition": True},
            "limits": _default_enterprise_limits(),
            "billing_cycle": "lifetime",
            "is_default": False,
            "is_active": True,
        },
    ]
    subscription_plan_table = sa.table(
        "subscription_plans",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("currency", sa.String()),
        sa.column("price_monthly", sa.Numeric()),
        sa.column("setup_fee_amount", sa.Numeric()),
        sa.column("features", postgresql.JSONB()),
        sa.column("limits", postgresql.JSONB()),
        sa.column("billing_cycle", sa.String()),
        sa.column("is_default", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )
    bind.execute(sa.insert(subscription_plan_table), plan_rows)

    system_setting_row = {
        "id": _system_setting_id(),
        "ai_enabled": True,
        "maintenance_mode": False,
        "max_upload_size_mb": 20,
        "allowed_file_types": ["pdf", "png", "jpg", "jpeg", "csv", "xlsx"],
        "default_currency": "KZT",
        "default_tax": 0,
        "notes": None,
    }
    system_settings_table = sa.table(
        "system_settings",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("ai_enabled", sa.Boolean()),
        sa.column("maintenance_mode", sa.Boolean()),
        sa.column("max_upload_size_mb", sa.Integer()),
        sa.column("allowed_file_types", postgresql.JSONB()),
        sa.column("default_currency", sa.String()),
        sa.column("default_tax", sa.Numeric()),
        sa.column("notes", sa.Text()),
    )
    bind.execute(sa.insert(system_settings_table), [system_setting_row])

    business_plan_id = _plan_id("business")
    now = datetime.now(UTC)
    company_ids = [row[0] for row in bind.execute(sa.text("SELECT id FROM companies")).all()]
    for company_id in company_ids:
        bind.execute(
            sa.text(
                "INSERT INTO company_subscriptions "
                "(id, created_at, updated_at, company_id, plan_id, status, trial_end, subscription_start, "
                "subscription_end, billing_disabled, setup_fee_paid, setup_fee_amount, setup_fee_paid_at, "
                "period_start, ai_requests_monthly, ai_tokens_monthly, ai_estimated_cost_monthly, "
                "recognition_count_monthly, average_recognition_time_ms, storage_usage_bytes, extra) "
                "VALUES (:id, :created_at, :updated_at, :company_id, :plan_id, :status, :trial_end, :subscription_start, "
                ":subscription_end, :billing_disabled, :setup_fee_paid, :setup_fee_amount, :setup_fee_paid_at, "
                ":period_start, 0, 0, 0, 0, 0, 0, '{}'::jsonb)"
            ),
            {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "updated_at": now,
                "company_id": company_id,
                "plan_id": business_plan_id,
                "status": "trialing",
                "trial_end": now + timedelta(days=14),
                "subscription_start": now,
                "subscription_end": None,
                "billing_disabled": False,
                "setup_fee_paid": False,
                "setup_fee_amount": 0,
                "setup_fee_paid_at": None,
                "period_start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            },
        )
        bind.execute(
            sa.text(
                "INSERT INTO company_usages "
                "(id, created_at, updated_at, company_id, period_start, period_end, monthly_ai_requests, "
                "monthly_token_usage, estimated_ai_cost, recognition_count, average_recognition_time_ms, storage_usage_bytes) "
                "VALUES (:id, :created_at, :updated_at, :company_id, :period_start, NULL, 0, 0, 0, 0, 0, 0)"
            ),
            {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "updated_at": now,
                "company_id": company_id,
                "period_start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            },
        )
        bind.execute(
            sa.text(
                "INSERT INTO notifications "
                "(id, created_at, updated_at, company_id, user_id, notification_type, title, message, status, read_at, payload) "
                "VALUES (:id, :created_at, :updated_at, :company_id, NULL, 'welcome', 'Welcome to Kara Orders', "
                "'Your subscription is ready. Explore your workspace and start creating orders.', 'unread', NULL, :payload::jsonb)"
            ),
            {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "updated_at": now,
                "company_id": company_id,
                "payload": "{}",
            },
        )


def downgrade() -> None:
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_status", table_name="notifications")
    op.drop_index("ix_notifications_company_status", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_company_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_company_usages_period", table_name="company_usages")
    op.drop_table("company_usages")

    op.drop_index("ix_company_subscriptions_company_plan", table_name="company_subscriptions")
    op.drop_index("ix_company_subscriptions_status", table_name="company_subscriptions")
    op.drop_table("company_subscriptions")

    op.drop_table("system_settings")

    op.drop_index("ix_subscription_plans_is_active", table_name="subscription_plans")
    op.drop_index("ix_subscription_plans_is_default", table_name="subscription_plans")
    op.drop_table("subscription_plans")

    op.drop_column("users", "is_super_admin")
