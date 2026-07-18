from __future__ import annotations

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


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


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


def test_product_catalog_crud_and_inventory_flow(client: TestClient) -> None:
    owner = _register_owner(
        client,
        company_name=f"Catalog {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@catalog.example.com",
    )
    access_token = owner["access_token"]

    category_response = client.post(
        "/api/v1/products/categories",
        headers=_auth_headers(access_token),
        json={"name": "Pipes", "slug": "pipes", "sort_order": 1},
    )
    assert category_response.status_code == 201, category_response.text
    category_id = category_response.json()["id"]

    tag_response = client.post(
        "/api/v1/products/tags",
        headers=_auth_headers(access_token),
        json={"name": "Plumbing", "slug": "plumbing", "color": "#0ea5e9"},
    )
    assert tag_response.status_code == 201, tag_response.text
    tag_id = tag_response.json()["id"]

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(access_token),
        json={
            "name": "PVC Pipe 20",
            "sku": "PIP-020",
            "barcode": "4820000000000",
            "category_id": category_id,
            "unit": "pcs",
            "currency": "KZT",
            "price": "1250.00",
            "cost": "800.00",
            "tax_rate": "12.00",
            "stock_qty": "20.00",
            "low_stock_threshold": "5.00",
            "tag_ids": [tag_id],
            "is_active": True,
        },
    )
    assert product_response.status_code == 201, product_response.text
    product = product_response.json()
    product_id = product["id"]
    assert product["tags"][0]["slug"] == "plumbing"
    assert product["category_rel"]["slug"] == "pipes"

    search_response = client.get(
        "/api/v1/products",
        headers=_auth_headers(access_token),
        params={"search": "4820000000000", "sort_by": "name"},
    )
    assert search_response.status_code == 200, search_response.text
    assert search_response.json()["total"] == 1

    inventory_response = client.get(f"/api/v1/products/{product_id}/inventory", headers=_auth_headers(access_token))
    assert inventory_response.status_code == 200, inventory_response.text
    assert inventory_response.json()["current_stock"] == "20.00"

    transaction_response = client.post(
        f"/api/v1/products/{product_id}/inventory/transactions",
        headers=_auth_headers(access_token),
        json={"transaction_type": "stock_out", "quantity": "5", "note": "Order #1001"},
    )
    assert transaction_response.status_code == 200, transaction_response.text
    assert transaction_response.json()["current_stock"] == "15.00"

    history_response = client.get(
        f"/api/v1/products/{product_id}/inventory/history",
        headers=_auth_headers(access_token),
    )
    assert history_response.status_code == 200, history_response.text
    assert history_response.json()[0]["transaction_type"] == "stock_out"

    update_response = client.patch(
        f"/api/v1/products/{product_id}",
        headers=_auth_headers(access_token),
        json={"name": "PVC Pipe 20 mm", "price": "1300.00"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["name"] == "PVC Pipe 20 mm"

    image_response = client.post(
        f"/api/v1/products/{product_id}/images",
        headers=_auth_headers(access_token),
        data={"alt_text": "Front view", "is_primary": "true"},
        files={"file": ("pipe.png", b"pipe-image", "image/png")},
    )
    assert image_response.status_code == 201, image_response.text
    assert image_response.json()["url"].startswith("https://storage.local/")

    delete_response = client.delete(f"/api/v1/products/{product_id}", headers=_auth_headers(access_token))
    assert delete_response.status_code == 200, delete_response.text

    restore_response = client.post(f"/api/v1/products/{product_id}/restore", headers=_auth_headers(access_token))
    assert restore_response.status_code == 200, restore_response.text

    get_response = client.get(f"/api/v1/products/{product_id}", headers=_auth_headers(access_token))
    assert get_response.status_code == 200, get_response.text


def test_product_rbac_and_company_isolation(client: TestClient, db_session) -> None:
    owner_a = _register_owner(
        client,
        company_name=f"Company {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@company-a.example.com",
    )
    owner_b = _register_owner(
        client,
        company_name=f"Company {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@company-b.example.com",
    )

    company_a = db_session.query(Company).filter(Company.id == owner_a["company"]["id"]).one()
    manager = _create_user(
        db_session,
        company_id=company_a.id,
        email=f"manager-{uuid4().hex[:8]}@company-a.example.com",
        password="Password123!",
        role=Role.MANAGER,
    )
    employee = _create_user(
        db_session,
        company_id=company_a.id,
        email=f"employee-{uuid4().hex[:8]}@company-a.example.com",
        password="Password123!",
        role=Role.EMPLOYEE,
    )

    owner_token = owner_a["access_token"]
    manager_token = _login(client, manager.email, "Password123!")
    employee_token = _login(client, employee.email, "Password123!")
    other_owner_token = owner_b["access_token"]

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(owner_token),
        json={"name": "Valve 1/2", "sku": "VAL-050", "unit": "pcs", "price": "4900.00"},
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]

    employee_create_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(employee_token),
        json={"name": "Denied", "sku": "DEN-001", "unit": "pcs", "price": "100.00"},
    )
    assert employee_create_response.status_code == 403

    manager_inventory_response = client.post(
        f"/api/v1/products/{product_id}/inventory/transactions",
        headers=_auth_headers(manager_token),
        json={"transaction_type": "stock_in", "quantity": "10"},
    )
    assert manager_inventory_response.status_code == 200, manager_inventory_response.text

    employee_list_response = client.get("/api/v1/products", headers=_auth_headers(employee_token))
    assert employee_list_response.status_code == 200, employee_list_response.text

    other_company_response = client.get(f"/api/v1/products/{product_id}", headers=_auth_headers(other_owner_token))
    assert other_company_response.status_code == 404
