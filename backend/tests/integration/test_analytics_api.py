from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.db.models.company import Company


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


def _invite_and_login(client, owner_token: str, email: str, role: str) -> dict[str, object]:
    invite_response = client.post(
        "/api/v1/companies/me/users/invitations",
        headers=_auth_headers(owner_token),
        json={"email": email, "full_name": "Team Member", "role": role},
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_token = invite_response.json()["invite_token"]

    accept_response = client.post(
        "/api/v1/companies/invitations/accept",
        json={
            "token": invite_token,
            "full_name": "Team Member",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert accept_response.status_code == 200, accept_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()


def test_analytics_endpoints_respect_rbac_and_export(client, db_session) -> None:
    owner = _register_owner(
        client,
        company_name=f"Analytics API {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@analytics-api.example.com",
    )
    owner_token = owner["access_token"]

    manager = _invite_and_login(
        client,
        owner_token,
        email=f"manager-{uuid4().hex[:8]}@analytics-api.example.com",
        role="manager",
    )
    employee = _invite_and_login(
        client,
        owner_token,
        email=f"employee-{uuid4().hex[:8]}@analytics-api.example.com",
        role="employee",
    )

    company = db_session.query(Company).filter(Company.id == owner["company"]["id"]).one()
    company.tax_percentage = Decimal("12.00")
    db_session.commit()

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(owner_token),
        json={
            "name": "Valve 1/2",
            "aliases": ["Valve Half Inch"],
            "sku": "VAL-050",
            "unit": "pcs",
            "price": "4900.00",
            "cost": "3000.00",
            "stock_qty": "8",
            "low_stock_threshold": "3",
        },
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]

    draft_response = client.post(
        "/api/v1/orders",
        headers=_auth_headers(owner_token),
        json={
            "customer_name": "Draft Customer",
            "customer_phone": "+7 700 111 22 33",
            "customer_address": "Almaty",
            "status": "draft",
            "items": [{"product_id": product_id, "quantity": "1", "discount_amount": "0"}],
        },
    )
    assert draft_response.status_code == 201, draft_response.text

    completed_response = client.post(
        "/api/v1/orders",
        headers=_auth_headers(owner_token),
        json={
            "customer_name": "Khan Market",
            "customer_phone": "+7 700 222 33 44",
            "customer_address": "Astana",
            "status": "completed",
            "items": [{"product_id": product_id, "quantity": "2", "discount_amount": "0"}],
        },
    )
    assert completed_response.status_code == 201, completed_response.text

    cancelled_response = client.post(
        "/api/v1/orders",
        headers=_auth_headers(owner_token),
        json={
            "customer_name": "Cancelled Customer",
            "customer_phone": "+7 700 333 44 55",
            "customer_address": "Shymkent",
            "status": "cancelled",
            "items": [{"product_id": product_id, "quantity": "1", "discount_amount": "0"}],
        },
    )
    assert cancelled_response.status_code == 201, cancelled_response.text

    dashboard_employee = client.get("/api/v1/dashboard", headers=_auth_headers(employee["access_token"]))
    assert dashboard_employee.status_code == 200, dashboard_employee.text

    analytics_employee = client.get("/api/v1/analytics/revenue", headers=_auth_headers(employee["access_token"]))
    assert analytics_employee.status_code == 403, analytics_employee.text

    revenue_response = client.get("/api/v1/analytics/revenue", headers=_auth_headers(manager["access_token"]))
    assert revenue_response.status_code == 200, revenue_response.text
    revenue_payload = revenue_response.json()
    assert revenue_payload["metrics"]["month_revenue"] == "10976.00"

    orders_response = client.get("/api/v1/analytics/orders", headers=_auth_headers(manager["access_token"]))
    assert orders_response.status_code == 200, orders_response.text
    assert orders_response.json()["status_breakdown"]["completed_orders"] == 1

    export_response = client.get(
        "/api/v1/analytics/export?format=csv",
        headers=_auth_headers(manager["access_token"]),
    )
    assert export_response.status_code == 200, export_response.text
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"analytics.csv\"" in export_response.headers["content-disposition"]
