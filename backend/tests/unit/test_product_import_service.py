from __future__ import annotations

import io
from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.user import User
from app.schemas.product_import import ProductImportConfirmRequest, ProductImportRow
from app.services.product_import_service import ProductImportService


def _build_service(db_session) -> ProductImportService:
    return ProductImportService(
        session=db_session,
        settings=Settings(database_url="postgresql+psycopg://example", supabase_storage_bucket="kara-orders"),
    )


def _create_company(db_session) -> Company:
    company = Company(name=f"Import {uuid4().hex[:6]}", currency="KZT", invoice_prefix="INV")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def test_parse_csv_auto_maps_columns_and_rows(db_session) -> None:
    service = _build_service(db_session)
    csv_content = (
        "Название,Цена,Категория,Производитель,Размер\n"
        "Труба,1200,Сантехника,Acme,20\n"
        "Муфта,340,Сантехника,Acme,\n"
        "Труба ППР 20 мм,900,Сантехника,Acme,\n"
    ).encode("utf-8")

    result = service.parse_excel(csv_content, "products.csv")

    assert result.mapping["Название"] == "name"
    assert result.mapping["Цена"] == "price"
    assert len(result.rows) == 3
    assert result.rows[0].name == "Труба"
    assert result.rows[0].price == Decimal("1200")
    assert result.rows[0].size == "20"
    assert result.rows[2].name == "Труба ППР"
    assert result.rows[2].size == "20 мм"


def test_confirm_import_formats_name_with_size(db_session) -> None:
    company = _create_company(db_session)
    service = _build_service(db_session)

    response = service.confirm_import(
        company.id,
        ProductImportConfirmRequest(
            rows=[
                ProductImportRow(name="Труба", price=Decimal("1200"), size="20"),
                ProductImportRow(name="Муфта", price=Decimal("340")),
            ]
        ),
    )

    assert response.created == 2
    assert response.errors == []

    products = service.product_service.list_products(company.id, page_size=10).items
    names = sorted(product.name for product in products)
    assert names == ["Муфта", "Труба - 20"]
    assert all(product.sku for product in products)


def test_parse_price_handles_localized_values() -> None:
    service = ProductImportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(database_url="postgresql+psycopg://example", supabase_storage_bucket="kara-orders"),
    )

    assert service._parse_price("1 200,50") == Decimal("1200.50")
    assert service._parse_price("4200") == Decimal("4200")
