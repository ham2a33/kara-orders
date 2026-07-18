from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.db.models.company import Company
from app.services.ai.service import AIService
from app.main import app
from app.services.ai.openai_provider import AIProviderResult, AIUsage


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


def test_ai_text_recognition_and_order_confirmation(client, db_session, monkeypatch) -> None:
    owner = _register_owner(
        client,
        company_name=f"AI Orders {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@ai-orders.example.com",
    )
    token = owner["access_token"]

    company = db_session.query(Company).filter(Company.id == owner["company"]["id"]).one()
    company.tax_percentage = Decimal("12.00")
    db_session.commit()

    product_response = client.post(
        "/api/v1/products",
        headers=_auth_headers(token),
        json={
            "name": "Valve 1/2",
            "aliases": ["Valve Half Inch"],
            "sku": "VAL-050",
            "unit": "pcs",
            "price": "4900.00",
        },
    )
    assert product_response.status_code == 201, product_response.text
    product_id = product_response.json()["id"]

    class FakeProvider:
        def extract_from_text(self, *args, **kwargs):
            return AIProviderResult(
                text='{"items":[{"product_name":"Valve Half Inch","quantity":2,"unit":"pcs","confidence":0.98}]}',
                raw_response={"id": "resp_1"},
                model="gpt-test",
                usage=AIUsage(input_tokens=11, output_tokens=20, total_tokens=31),
            )

    monkeypatch.setattr(AIService, "_provider", lambda self: FakeProvider())

    recognition_response = client.post(
        "/api/v1/ai/order-recognitions/text",
        headers=_auth_headers(token),
        json={"text": "Valve Half Inch 2"},
    )
    assert recognition_response.status_code == 201, recognition_response.text
    recognition = recognition_response.json()
    recognition_id = recognition["id"]
    assert recognition["status"] == "completed"
    assert recognition["items"][0]["matched_product"]["id"] == product_id

    confirm_response = client.post(
        f"/api/v1/ai/order-recognitions/{recognition_id}/confirm",
        headers=_auth_headers(token),
        json={
            "customer_name": "Khan Market",
            "customer_phone": "+7 700 000 00 00",
            "customer_address": "Almaty",
            "notes": "Deliver today",
            "items": [{"product_id": product_id, "quantity": "2", "discount_amount": "0"}],
        },
    )
    assert confirm_response.status_code == 200, confirm_response.text
    confirm_data = confirm_response.json()
    assert confirm_data["recognition"]["status"] == "converted"
    assert confirm_data["order"]["total"] == "10976.00"

    history_response = client.get("/api/v1/ai/order-recognitions", headers=_auth_headers(token))
    assert history_response.status_code == 200, history_response.text
    assert history_response.json()["total"] == 1


def test_ai_pdf_recognition_uses_storage(client, monkeypatch) -> None:
    owner = _register_owner(
        client,
        company_name=f"AI PDFs {uuid4().hex[:8]}",
        email=f"owner-{uuid4().hex[:8]}@ai-pdfs.example.com",
    )
    token = owner["access_token"]

    class FakeProvider:
        def extract_from_file(self, *args, **kwargs):
            return AIProviderResult(
                text='{"items":[{"product_name":"Cable 10m","quantity":3,"unit":"pcs","confidence":0.95}]}',
                raw_response={"id": "resp_pdf"},
                model="gpt-test",
                usage=AIUsage(input_tokens=14, output_tokens=18, total_tokens=32),
            )

    monkeypatch.setattr(AIService, "_provider", lambda self: FakeProvider())

    response = client.post(
        "/api/v1/ai/order-recognitions/pdf",
        headers=_auth_headers(token),
        files={"file": ("supplier.pdf", b"%PDF-1.4\n%stub", "application/pdf")},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["input_type"] == "pdf"
    assert payload["original_file_path"].startswith(str(owner["company"]["id"]))
