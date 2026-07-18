from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import Role
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.user import User
from app.dependencies.auth import get_current_user, require_company_access, require_roles
from app.dependencies.deps import get_app_settings, get_db


def _build_guarded_client(test_session_factory, test_settings) -> TestClient:
    guarded_app = FastAPI()

    @guarded_app.get("/admin-only")
    def admin_only(current_user=Depends(require_roles(Role.ADMIN))):
        return {"email": current_user.email}

    @guarded_app.get("/companies/{company_id}")
    def company_scope(current_user=Depends(require_company_access)):
        return {"company_id": str(current_user.company_id)}

    def override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    guarded_app.dependency_overrides[get_db] = override_get_db
    guarded_app.dependency_overrides[get_app_settings] = lambda: test_settings
    guarded_app.dependency_overrides[get_current_user] = get_current_user
    return TestClient(guarded_app)


def _create_user(session, *, company_name: str, email: str, password: str, role: str) -> tuple[Company, User]:
    company = Company(name=company_name, currency="KZT", invoice_prefix="INV")
    session.add(company)
    session.flush()

    user = User(
        company_id=company.id,
        email=email,
        password_hash=hash_password(password),
        full_name=email.split("@", 1)[0],
        role=role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(company)
    session.refresh(user)
    return company, user


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_register_login_refresh_logout_flow(client: TestClient) -> None:
    payload = {
        "company_name": f"Acme {uuid4().hex[:8]}",
        "full_name": "Owner User",
        "email": f"owner-{uuid4().hex[:8]}@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201, register_response.text
    register_data = register_response.json()
    assert register_data["user"]["role"] == "owner"
    assert register_data["company"]["name"] == payload["company_name"]
    assert register_data["access_token"]
    assert "kara_orders_refresh_token" in register_response.headers.get("set-cookie", "")

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200, login_response.text
    login_data = login_response.json()
    assert login_data["access_token"]
    assert login_data["access_token"] != register_data["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    me_data = me_response.json()
    assert me_data["user"]["email"] == payload["email"]
    assert me_data["company"]["name"] == payload["company_name"]

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200, refresh_response.text
    assert refresh_response.json()["access_token"] != login_data["access_token"]

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200, logout_response.text
    assert logout_response.json()["detail"] == "Logged out"
    assert "Max-Age=0" in logout_response.headers.get("set-cookie", "")

    refresh_after_logout = client.post("/api/v1/auth/refresh")
    assert refresh_after_logout.status_code == 401


def test_protected_route_rejects_unauthorized_users(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_health_endpoints_are_available(client: TestClient) -> None:
    live_response = client.get("/api/v1/health/live")
    assert live_response.status_code == 200
    assert live_response.json()["status"] == "alive"

    ready_response = client.get("/api/v1/health/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["status"] == "ready"


def test_rbac_permissions(test_session_factory, test_settings) -> None:
    session = test_session_factory()
    try:
        company, _ = _create_user(
            session,
            company_name="RBAC Co",
            email="owner@rbac.local",
            password="Password123!",
            role=Role.OWNER.value,
        )
        _, admin = _create_user(
            session,
            company_name="RBAC Admin",
            email="admin@rbac.local",
            password="Admin123!Password",
            role=Role.ADMIN.value,
        )
        _, employee = _create_user(
            session,
            company_name="RBAC Employee",
            email="employee@rbac.local",
            password="Employee123!Password",
            role=Role.EMPLOYEE.value,
        )
    finally:
        session.close()

    with _build_guarded_client(test_session_factory, test_settings) as guarded_client:
        admin_token = _login(guarded_client, admin.email, "Admin123!Password")
        employee_token = _login(guarded_client, employee.email, "Employee123!Password")

        admin_response = guarded_client.get(
            "/admin-only",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_response.status_code == 200, admin_response.text

        employee_response = guarded_client.get(
            "/admin-only",
            headers={"Authorization": f"Bearer {employee_token}"},
        )
        assert employee_response.status_code == 403


def test_company_isolation(test_session_factory, test_settings) -> None:
    session = test_session_factory()
    try:
        company_a, user_a = _create_user(
            session,
            company_name="Company A",
            email="user-a@company.local",
            password="Password123!",
            role=Role.MANAGER.value,
        )
        company_b, _ = _create_user(
            session,
            company_name="Company B",
            email="user-b@company.local",
            password="Password123!",
            role=Role.EMPLOYEE.value,
        )
    finally:
        session.close()

    with _build_guarded_client(test_session_factory, test_settings) as guarded_client:
        token_a = _login(guarded_client, user_a.email, "Password123!")

        same_company_response = guarded_client.get(
            f"/companies/{company_a.id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert same_company_response.status_code == 200, same_company_response.text

        other_company_response = guarded_client.get(
            f"/companies/{company_b.id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert other_company_response.status_code == 403
