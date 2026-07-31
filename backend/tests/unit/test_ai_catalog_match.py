from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.ai import AIExtractionItem
from app.services.ai.catalog_match import (
    composite_search_key,
    normalize_catalog_search_text,
    rank_catalog_matches,
)
from app.services.ai.product_matcher import ProductMatcher


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


def test_catalog_match_finds_product_by_short_name_and_diameter(db_session) -> None:
    company = _create_company(db_session)
    product = Product(
        company_id=company.id,
        name="Труба ППР 20 мм",
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Труба",
                size="20",
                quantity=Decimal("20"),
                unit="шт",
                confidence=Decimal("1"),
                source_line="Труба 20 20 шт",
            )
        ],
    )
    assert matched[0].status == "matched"
    assert matched[0].selected_product is not None
    assert matched[0].selected_product.id == product.id


def test_catalog_match_finds_pipe_when_order_qty_in_meters(db_session) -> None:
    company = _create_company(db_session)
    product = Product(
        company_id=company.id,
        name="Труба ППР 20 мм",
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Труба",
                size="20 м",
                quantity=Decimal("20"),
                unit="м",
                confidence=Decimal("1"),
                source_line="Труба 20 20м",
            )
        ],
    )
    assert matched[0].status == "matched"
    assert matched[0].selected_product is not None
    assert matched[0].selected_product.id == product.id


def test_catalog_match_finds_kran_by_short_name_and_diameter(db_session) -> None:
    company = _create_company(db_session)
    product = Product(
        company_id=company.id,
        name="Кран 20 мм",
        unit="pcs",
        currency="KZT",
        price=Decimal("2500.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Кран",
                size="20",
                quantity=Decimal("2"),
                unit="шт",
                confidence=Decimal("1"),
                source_line="Кран 20 2 шт",
            )
        ],
    )
    assert matched[0].status == "matched"
    assert matched[0].selected_product is not None
    assert matched[0].selected_product.id == product.id


def test_catalog_match_marks_not_found(db_session) -> None:
    company = _create_company(db_session)
    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Unknown",
                size="99",
                quantity=Decimal("1"),
                unit="шт",
                confidence=Decimal("1"),
                source_line="Unknown 99 1 шт",
            )
        ],
    )
    assert matched[0].status == "not_found"
    assert matched[0].candidate_products == []
    assert matched[0].match_diagnostics is not None
    assert matched[0].match_diagnostics.get("failure_reason")


def test_catalog_match_returns_multiple_fuzzy_pipe_variants(db_session) -> None:
    company = _create_company(db_session)
    db_session.add_all(
        [
            Product(
                company_id=company.id,
                name="Труба ППР 20 мм",
                unit="pcs",
                currency="KZT",
                price=Decimal("100.00"),
                is_active=True,
            ),
            Product(
                company_id=company.id,
                name="Труба PN20 20 мм",
                unit="pcs",
                currency="KZT",
                price=Decimal("110.00"),
                is_active=True,
            ),
        ]
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
    assert matched[0].selected_product is not None
    assert len(matched[0].candidate_products) == 1


def _catalog_product(company: Company, name: str, *, size: str | None = None) -> Product:
    return Product(
        company_id=company.id,
        name=name,
        size=size,
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        is_active=True,
    )


def test_rank_catalog_match_pipe_dash_size_in_name(db_session) -> None:
    company = _create_company(db_session)
    product = _catalog_product(company, "Труба - 20")
    db_session.add(product)
    db_session.commit()

    matches = rank_catalog_matches([product], query_name="Труба", query_size="20")
    assert len(matches) == 1
    assert matches[0].profile.product.id == product.id
    assert matches[0].size_match is True


def test_rank_catalog_match_prefers_matching_diameter(db_session) -> None:
    company = _create_company(db_session)
    pipe_20 = _catalog_product(company, "Труба - 20")
    pipe_25 = _catalog_product(company, "Труба - 25")
    db_session.add_all([pipe_20, pipe_25])
    db_session.commit()

    matches = rank_catalog_matches([pipe_20, pipe_25], query_name="Труба", query_size="25")
    assert len(matches) == 1
    assert matches[0].profile.product.id == pipe_25.id


def test_rank_catalog_match_cable_length_in_name(db_session) -> None:
    company = _create_company(db_session)
    product = _catalog_product(company, "Кабель 10 метров")
    db_session.add(product)
    db_session.commit()

    matches = rank_catalog_matches([product], query_name="Кабель", query_size="10")
    assert len(matches) == 1
    assert matches[0].profile.product.id == product.id


def test_catalog_match_pipe_dash_name_via_matcher(db_session) -> None:
    company = _create_company(db_session)
    product = _catalog_product(company, "Труба - 20")
    db_session.add(product)
    db_session.commit()

    matcher = ProductMatcher(db_session, low_confidence_threshold=Decimal("0.75"))
    matched = matcher.match_items(
        company.id,
        [
            AIExtractionItem(
                product_name="Труба",
                size="20",
                quantity=Decimal("20"),
                unit="м",
                confidence=Decimal("1"),
                source_line="Труба 20 20м",
            )
        ],
    )
    assert matched[0].status == "matched"
    assert matched[0].selected_product is not None
    assert matched[0].selected_product.id == product.id


def test_normalize_catalog_search_text_strips_units() -> None:
    assert normalize_catalog_search_text("Кабель 10 метров") == normalize_catalog_search_text("Кабель 10")
    assert composite_search_key("Труба", "20") == normalize_catalog_search_text("Труба - 20")
