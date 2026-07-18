from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.db.models.company import Company
from app.db.models.company_subscription import CompanySubscription
from app.db.models.subscription_plan import SubscriptionPlan
from app.services.platform_service import PlatformService


def _create_company(db_session) -> Company:
    company = Company(
        name=f"Platform Co {uuid4().hex[:6]}",
        currency="KZT",
        invoice_prefix="INV",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def test_platform_service_creates_default_subscription_and_usage(db_session) -> None:
    company = _create_company(db_session)
    service = PlatformService(db_session)

    subscription = service.get_or_create_default_subscription(company)
    assert subscription.plan.slug == "business"
    assert subscription.status == "trialing"

    service.record_ai_usage(
        company.id,
        tokens_used=15,
        recognition_time_ms=125,
        estimated_cost=Decimal("0.25"),
    )

    overview = service.get_subscription_overview(company.id)
    assert overview.usage.monthly_ai_requests == 1
    assert overview.usage.monthly_token_usage == 15
    assert overview.usage.recognition_count == 1
    assert overview.subscription.ai_requests_monthly == 1
    assert overview.subscription.ai_tokens_monthly == 15


def test_platform_service_enforces_limits_and_logs_audit(db_session) -> None:
    company = _create_company(db_session)
    service = PlatformService(db_session)
    subscription = service.get_or_create_default_subscription(company)

    custom_plan = SubscriptionPlan(
        slug=f"tiny-{uuid4().hex[:8]}",
        name="Tiny",
        description="Tiny test plan",
        currency="KZT",
        price_monthly=Decimal("1"),
        setup_fee_amount=Decimal("0"),
        features={"analytics": True},
        limits={"maximum_ai_requests": 0},
        billing_cycle="monthly",
        is_default=False,
        is_active=True,
    )
    db_session.add(custom_plan)
    db_session.commit()
    db_session.refresh(custom_plan)

    subscription.plan_id = custom_plan.id
    db_session.commit()

    with pytest.raises(ValidationAppError):
        service.ensure_limit(company.id, "maximum_ai_requests")

    notification_response = service.get_notifications(company.id)
    assert notification_response.total >= 1

    service.log_action(
        action="plan_changed",
        company_id=company.id,
        actor_user_id=None,
        resource_type="subscription",
        resource_id=str(subscription.id),
        description="Plan changed in test",
    )
    audit_logs = service.get_audit_logs(company_id=company.id)
    assert audit_logs.total >= 1
