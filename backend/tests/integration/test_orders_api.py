from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.auth import Role
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.user import User


def _register_owner(client: TestClient, *, company_name: str, email: str) -> dict[str, object]:
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


def _create_user(session, *, company_id, email: str, password: str, role: Role) -> User:
    user = User(
        company_id=company_id,
        email=email,
        password_hash=hash_password(password),
        full_name=email.split("@", 1)[0],
        role=role.value,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_order_crud_and_invoice_generation(client: TestClient, db_session) -> None:
    owner = _register_owner(
        client,
        company_name=f"Orders {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@orders.example.com",
    )
    owner_token = owner["access_token"]

    company = db_session.query(Company).filter(Company.id == owner["company"]["id"]).one()
    company.tax_percentage = Decimal("12.00")
    db_session.commit()

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(owner_token),
        json={"name": "PVC Pipe 20", "sku": "PIP-020", "unit": "pcs", "price": "100.00"},
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]

    order_response = client.post(
        "/api/v1/orders",
        headers=_auth_headers(owner_token),
        json={
            "customer_name": "Khan Market",
            "customer_phone": "+7 700 000 00 00",
            "customer_address": "Almaty",
            "notes": "Deliver quickly",
            "items": [
                {"product_id": product_id, "quantity": "2", "discount_amount": "10"},
            ],
        },
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    order_id = order["id"]
    assert order["subtotal"] == "200.00"
    assert order["discount_total"] == "10.00"
    assert order["tax_total"] == "22.80"
    assert order["total"] == "212.80"
    assert order["items"][0]["line_total"] == "212.80"

    list_response = client.get("/api/v1/orders", headers=_auth_headers(owner_token))
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] == 1

    preview_response = client.get(f"/api/v1/orders/{order_id}/invoice/preview", headers=_auth_headers(owner_token))
    assert preview_response.status_code == 200, preview_response.text
    assert preview_response.json()["company_name"] == company.name

    pdf_response = client.get(f"/api/v1/orders/{order_id}/invoice/pdf", headers=_auth_headers(owner_token))
    assert pdf_response.status_code == 200, pdf_response.text
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert pdf_response.content.startswith(b"%PDF")

    update_response = client.patch(
        f"/api/v1/orders/{order_id}",
        headers=_auth_headers(owner_token),
        json={"status": "confirmed"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["status"] == "confirmed"

    employee_user = _create_user(
        db_session,
        company_id=company.id,
        email=f"employee-{uuid4().hex[:8]}@orders.example.com",
        password="Password123!",
        role=Role.EMPLOYEE,
    )
    employee_login = client.post(
        "/api/v1/auth/login",
        json={"email": employee_user.email, "password": "Password123!"},
    )
    assert employee_login.status_code == 200, employee_login.text
    employee_token = employee_login.json()["access_token"]

    delete_response = client.delete(f"/api/v1/orders/{order_id}", headers=_auth_headers(employee_token))
    assert delete_response.status_code == 403

    admin_user = _create_user(
        db_session,
        company_id=company.id,
        email=f"admin-{uuid4().hex[:8]}@orders.example.com",
        password="Password123!",
        role=Role.ADMIN,
    )
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "Password123!"},
    )
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    admin_delete_response = client.delete(f"/api/v1/orders/{order_id}", headers=_auth_headers(admin_token))
    assert admin_delete_response.status_code == 200, admin_delete_response.text

    restore_response = client.post(f"/api/v1/orders/{order_id}/restore", headers=_auth_headers(admin_token))
    assert restore_response.status_code == 200, restore_response.text


def test_order_company_isolation(client: TestClient) -> None:
    owner_a = _register_owner(
        client,
        company_name=f"Alpha {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@alpha.example.com",
    )
    owner_b = _register_owner(
        client,
        company_name=f"Beta {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@beta.example.com",
    )

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(owner_a["access_token"]),
        json={"name": "Valve 1/2", "sku": "VAL-050", "unit": "pcs", "price": "4900.00"},
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]

    order_response = client.post(
        "/api/v1/orders",
        headers=_auth_headers(owner_a["access_token"]),
        json={
            "customer_name": "Alpha Customer",
            "items": [{"product_id": product_id, "quantity": "1"}],
        },
    )
    assert order_response.status_code == 201, order_response.text
    order_id = order_response.json()["id"]

    other_company_response = client.get(f"/api/v1/orders/{order_id}", headers=_auth_headers(owner_b["access_token"]))
    assert other_company_response.status_code == 404
