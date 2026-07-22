from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.ai import AIExtractionItem, AITextRecognitionRequest
from app.services.ai.openai_provider import AIProviderResult, AIUsage
from app.services.ai.product_matcher import ProductMatcher
from app.services.ai.service import AIService


def _create_company(db_session) -> Company:
    company = Company(
        name=f"AI Co {uuid4().hex[:6]}",
        currency="KZT",
        invoice_prefix="INV",
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def _create_owner(db_session, company: Company) -> User:
    user = User(
        company_id=company.id,
        email=f"owner-{uuid4().hex[:6]}@ai.example.com",
        password_hash=hash_password("Password123!"),
        full_name="Owner",
        role=Role.OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_product_matcher_matches_aliases_and_auto_selects_single_candidate(db_session) -> None:
    company = _create_company(db_session)
    product = Product(
        company_id=company.id,
        name="PVC Pipe 20",
        aliases=["Pipe 20mm", "Pipe twenty"],
        sku="PIP-020",
        barcode="123456789",
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched_items = matcher.match_items(
        company.id,
        [
            AIExtractionItem(product_name="Pipe 20mm", quantity=Decimal("2"), unit="pcs", confidence=Decimal("0.92")),
            AIExtractionItem(product_name="Pipe 20", quantity=Decimal("1"), unit="pcs", confidence=Decimal("0.62")),
        ],
    )

    assert matched_items[0].matched_product.id == product.id
    assert matched_items[0].status == "matched"
    assert matched_items[1].selected_product.id == product.id
    assert matched_items[1].status == "matched"


def test_product_matcher_returns_multiple_candidates(db_session) -> None:
    company = _create_company(db_session)
    products = [
        Product(
            company_id=company.id,
            name="Pipe 20 mm",
            manufacturer="KAZPIPE",
            unit="pcs",
            currency="KZT",
            price=Decimal("1200.00"),
            stock_qty=Decimal("43"),
            is_active=True,
        ),
        Product(
            company_id=company.id,
            name="Pipe 20 mm",
            manufacturer="SteelPro",
            unit="pcs",
            currency="KZT",
            price=Decimal("1180.00"),
            stock_qty=Decimal("21"),
            is_active=True,
        ),
    ]
    db_session.add_all(products)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched_items = matcher.match_items(
        company.id,
        [AIExtractionItem(product_name="Pipe 20 mm", quantity=Decimal("15"), unit="pcs", confidence=Decimal("0.99"))],
    )

    assert len(matched_items[0].candidate_products) == 2
    assert matched_items[0].selected_product is None
    assert matched_items[0].status == "needs_review"


def test_ai_service_text_recognition_uses_catalog_matches(db_session, monkeypatch) -> None:
    company = _create_company(db_session)
    owner = _create_owner(db_session, company)
    product = Product(
        company_id=company.id,
        name="Valve 1/2",
        aliases=["Valve Half Inch"],
        sku="VAL-050",
        barcode="987654321",
        unit="pcs",
        currency="KZT",
        price=Decimal("4900.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    settings = Settings(
        database_url="postgresql+psycopg://example",
        secret_key="test-secret",
        cors_origins=["http://testserver"],
    )
    service = AIService(db_session, settings)

    class FakeProvider:
        def extract_from_text(self, *args, **kwargs):
            return AIProviderResult(
                text='{"items":[{"product_name":"Valve Half Inch","quantity":2,"unit":"pcs","confidence":0.98}]}',
                raw_response={"id": "resp_1"},
                model="gpt-test",
                usage=AIUsage(input_tokens=10, output_tokens=20, total_tokens=30),
            )

    monkeypatch.setattr(service, "_provider", lambda: FakeProvider())

    result = service.recognize_text(company.id, owner, AITextRecognitionRequest(text="Valve Half Inch 2"))
    assert result.status == "completed"
    assert result.items[0].matched_product is not None
    assert result.items[0].matched_product.id == product.id
    assert result.tokens_used == 30
    assert result.original_text == "Valve Half Inch 2"
