from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.db.models.company_subscription import CompanySubscription
from app.db.models.subscription_plan import SubscriptionPlan
from app.db.models.user import User


def _register_owner(client, *, company_name: str, email: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": company_name,
            "full_name": "Owner User",
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_platform_subscription_usage_notifications_and_admin_flow(client, db_session) -> None:
    owner = _register_owner(
        client,
        company_name=f"Platform {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@platform.example.com",
    )
    token = owner["access_token"]
    company_id = owner["company"]["id"]

    subscription_response = client.get("/api/v1/platform/subscriptions/me", headers=_auth_headers(token))
    assert subscription_response.status_code == 200, subscription_response.text
    assert subscription_response.json()["subscription"]["plan"]["slug"] == "business"

    usage_response = client.get("/api/v1/platform/usage/me", headers=_auth_headers(token))
    assert usage_response.status_code == 200, usage_response.text

    billing_response = client.get("/api/v1/platform/billing/me", headers=_auth_headers(token))
    assert billing_response.status_code == 200, billing_response.text

    notifications_response = client.get("/api/v1/platform/notifications", headers=_auth_headers(token))
    assert notifications_response.status_code == 200, notifications_response.text
    notifications = notifications_response.json()["items"]
    assert notifications

    mark_read_response = client.post(
        f"/api/v1/platform/notifications/{notifications[0]['id']}/read",
        headers=_auth_headers(token),
    )
    assert mark_read_response.status_code == 200, mark_read_response.text
    assert mark_read_response.json()["status"] == "read"

    audit_response = client.get("/api/v1/platform/audit", headers=_auth_headers(token))
    assert audit_response.status_code == 200, audit_response.text
    assert audit_response.json()["total"] >= 1

    admin_response = client.get("/api/v1/platform/admin/companies", headers=_auth_headers(token))
    assert admin_response.status_code == 403

    user = db_session.query(User).filter(User.id == owner["user"]["id"]).one()
    user.is_super_admin = True
    db_session.commit()

    admin_response = client.get("/api/v1/platform/admin/companies", headers=_auth_headers(token))
    assert admin_response.status_code == 200, admin_response.text
    assert admin_response.json()["items"]

    settings_response = client.patch(
        "/api/v1/platform/system/settings",
        headers=_auth_headers(token),
        json={
            "ai_enabled": True,
            "maintenance_mode": False,
            "max_upload_size_mb": 25,
            "allowed_file_types": ["pdf", "png", "jpg"],
            "default_currency": "KZT",
            "default_tax": "12.50",
            "notes": "Updated in test",
        },
    )
    assert settings_response.status_code == 200, settings_response.text
    assert settings_response.json()["max_upload_size_mb"] == 25

    plan_response = client.get("/api/v1/platform/plans", headers=_auth_headers(token))
    assert plan_response.status_code == 200, plan_response.text
    assert any(plan["slug"] == "business" for plan in plan_response.json()["items"])

    company_isolation_response = client.get("/api/v1/platform/admin/companies", headers=_auth_headers(owner["access_token"]))
    assert company_isolation_response.status_code == 200


def test_platform_plan_limit_enforcement_blocks_products(client, db_session) -> None:
    owner = _register_owner(
        client,
        company_name=f"Limited {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@limited.example.com",
    )
    token = owner["access_token"]

    custom_plan = SubscriptionPlan(
        slug=f"limited-{uuid4().hex[:8]}",
        name="Limited",
        description="Limited plan",
        currency="KZT",
        price_monthly=Decimal("1"),
        setup_fee_amount=Decimal("0"),
        features={"analytics": True},
        limits={"maximum_products": 0},
        billing_cycle="monthly",
        is_default=False,
        is_active=True,
    )
    db_session.add(custom_plan)
    db_session.commit()
    db_session.refresh(custom_plan)

    subscription = db_session.query(CompanySubscription).filter(CompanySubscription.company_id == owner["company"]["id"]).one()
    subscription.plan_id = custom_plan.id
    db_session.commit()

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(token),
        json={"name": "Blocked product", "sku": "BLK-001", "unit": "pcs", "price": "10.00"},
    )
    assert product_response.status_code == 422, product_response.text
