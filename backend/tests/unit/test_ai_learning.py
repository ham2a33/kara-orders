from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.schemas.ai import AIExtractionItem
from app.services.ai.learning_service import AILearningService
from app.services.ai.product_matcher import ProductMatcher
from app.db.models.company import Company
from app.db.models.product import Product


def _company(db_session) -> Company:
    company = Company(name=f"Co {uuid4().hex[:6]}", currency="KZT", invoice_prefix="INV")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def test_learning_skips_fuzzy_when_mapping_exists(db_session) -> None:
    company = _company(db_session)
    product = Product(
        company_id=company.id,
        name="Труба ППР 20 мм",
        unit="pcs",
        currency="KZT",
        price=Decimal("100"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    learning = AILearningService(db_session)
    learning.remember_manual_selection(
        company.id,
        ocr_text="Труба 20 5 шт",
        product_name="Труба",
        size="20",
        product_id=product.id,
    )
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Труба",
                size="20",
                quantity=Decimal("5"),
                unit="шт",
                confidence=Decimal("1"),
                source_line="Труба 20 5 шт",
            )
        ],
    )
    assert matched[0].status == "matched"
    assert matched[0].match_method == "learned"
    assert matched[0].selected_product is not None
    assert matched[0].selected_product.id == product.id
