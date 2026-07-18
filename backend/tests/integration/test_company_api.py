from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.auth import Role


def _register_owner(client: TestClient, *, company_name: str, email: str) -> tuple[str, str]:
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
    data = response.json()
    return data["access_token"], data["user"]["id"]


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_company_profile_settings_and_logo_upload(client: TestClient) -> None:
    access_token, _ = _register_owner(
        client,
        company_name=f"Acme {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@acme.local",
    )

    profile_response = client.get("/api/v1/companies/me", headers=_auth_headers(access_token))
    assert profile_response.status_code == 200, profile_response.text

    update_payload = {
        "name": "Acme Supplies",
        "email": "billing@acme.local",
        "website": "https://acme.local",
        "timezone": "Asia/Almaty",
        "language": "en",
        "bin_tax_id": "123456789012",
        "currency": "KZT",
        "address": "Almaty, Kazakhstan",
        "phone": "+7 700 000 00 00",
        "invoice_prefix": "ACM",
        "invoice_number_format": "{prefix}-{number:05d}",
        "tax_percentage": 12.5,
        "footer_text": "Thanks for your business.",
        "payment_information": "Kaspi Bank",
        "notes": "Handle with care.",
    }
    update_response = client.patch(
        "/api/v1/companies/me",
        headers=_auth_headers(access_token),
        json=update_payload,
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["name"] == "Acme Supplies"
    assert updated["invoice_prefix"] == "ACM"
    assert updated["tax_percentage"] == 12.5

    logo_response = client.post(
        "/api/v1/companies/me/logo",
        headers=_auth_headers(access_token),
        files={"file": ("logo.png", b"logo-bytes", "image/png")},
    )
    assert logo_response.status_code == 200, logo_response.text
    assert logo_response.json()["url"].startswith("https://storage.local/")

    invoice_logo_response = client.post(
        "/api/v1/companies/me/invoice-logo",
        headers=_auth_headers(access_token),
        files={"file": ("invoice-logo.png", b"invoice-logo", "image/png")},
    )
    assert invoice_logo_response.status_code == 200, invoice_logo_response.text

    refreshed_response = client.get("/api/v1/companies/me", headers=_auth_headers(access_token))
    refreshed = refreshed_response.json()
    assert refreshed["logo_url"].startswith("https://storage.local/")
    assert refreshed["invoice_logo_url"].startswith("https://storage.local/")


def test_user_invitations_roles_and_isolation(client: TestClient) -> None:
    owner_access_token, _ = _register_owner(
        client,
        company_name=f"Team {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@team.local",
    )

    invite_response = client.post(
        "/api/v1/companies/me/users/invitations",
        headers=_auth_headers(owner_access_token),
        json={
            "email": f"admin-{uuid4().hex[:8]}@team.local",
            "full_name": "Invited Admin",
            "role": Role.ADMIN.value,
        },
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_data = invite_response.json()
    assert invite_data["invitation"]["email"].endswith("@team.local")
    assert invite_data["invite_token"]

    invitations_response = client.get(
        "/api/v1/companies/me/users/invitations",
        headers=_auth_headers(owner_access_token),
    )
    assert invitations_response.status_code == 200, invitations_response.text
    assert invitations_response.json()["items"]

    accept_response = client.post(
        "/api/v1/companies/invitations/accept",
        json={
            "token": invite_data["invite_token"],
            "full_name": "Invited Admin",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert accept_response.status_code == 200, accept_response.text
    invited_user_id = accept_response.json()["id"]

    admin_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": invite_data["invitation"]["email"], "password": "Password123!"},
    )
    assert admin_login_response.status_code == 200, admin_login_response.text
    admin_access_token = admin_login_response.json()["access_token"]

    users_response = client.get(
        "/api/v1/companies/me/users",
        headers=_auth_headers(admin_access_token),
    )
    assert users_response.status_code == 200, users_response.text
    assert len(users_response.json()["items"]) >= 2

    change_role_response = client.patch(
        f"/api/v1/companies/me/users/{invited_user_id}/role",
        headers=_auth_headers(owner_access_token),
        json={"role": Role.MANAGER.value},
    )
    assert change_role_response.status_code == 200, change_role_response.text
    assert change_role_response.json()["role"] == Role.MANAGER.value

    second_owner_access_token, second_owner_id = _register_owner(
        client,
        company_name=f"Other {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@other.local",
    )
    assert second_owner_id

    isolation_response = client.patch(
        f"/api/v1/companies/me/users/{second_owner_id}/role",
        headers=_auth_headers(owner_access_token),
        json={"role": Role.EMPLOYEE.value},
    )
    assert isolation_response.status_code == 404

    employee_invite_response = client.post(
        "/api/v1/companies/me/users/invitations",
        headers=_auth_headers(owner_access_token),
        json={
            "email": f"employee-{uuid4().hex[:8]}@team.local",
            "full_name": "Invited Employee",
            "role": Role.EMPLOYEE.value,
        },
    )
    assert employee_invite_response.status_code == 201, employee_invite_response.text
    employee_token = employee_invite_response.json()["invite_token"]
    employee_accept_response = client.post(
        "/api/v1/companies/invitations/accept",
        json={
            "token": employee_token,
            "full_name": "Invited Employee",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert employee_accept_response.status_code == 200, employee_accept_response.text
    employee_email = employee_invite_response.json()["invitation"]["email"]
    employee_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": employee_email, "password": "Password123!"},
    )
    assert employee_login_response.status_code == 200, employee_login_response.text
    employee_access_token = employee_login_response.json()["access_token"]

    employee_settings_response = client.patch(
        "/api/v1/companies/me",
        headers=_auth_headers(employee_access_token),
        json={"name": "Should Fail"},
    )
    assert employee_settings_response.status_code == 403
