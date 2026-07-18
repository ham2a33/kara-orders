from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.product import (
    ProductCategoryCreateRequest,
    ProductInventoryTransactionCreateRequest,
)
from app.services.product_service import ProductService


class FakeStorage:
    def upload_public_file(self, *, bucket: str, object_path: str, content: bytes, content_type: str):
        return type("UploadResult", (), {"public_url": f"https://storage.local/{bucket}/{object_path}", "object_path": object_path})()


def _build_service(db_session) -> ProductService:
    return ProductService(
        session=db_session,
        settings=Settings(database_url="postgresql+psycopg://example", supabase_storage_bucket="kara-orders"),
        storage_service=FakeStorage(),
    )


def _create_company_and_user(db_session) -> tuple[Company, User]:
    company = Company(name=f"Acme {uuid4().hex[:6]}", currency="KZT", invoice_prefix="INV")
    db_session.add(company)
    db_session.flush()
    user = User(
        company_id=company.id,
        email=f"owner-{uuid4().hex[:6]}@acme.local",
        password_hash=hash_password("Password123!"),
        full_name="Owner",
        role=Role.OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(company)
    db_session.refresh(user)
    return company, user


def test_product_service_inventory_calculation(db_session) -> None:
    company, actor = _create_company_and_user(db_session)
    product = Product(
        company_id=company.id,
        name="PVC Pipe 20",
        sku="PIP-020",
        unit="pcs",
        currency="KZT",
        price=Decimal("1250.00"),
        cost=Decimal("800.00"),
        stock_qty=Decimal("10.00"),
        low_stock_threshold=Decimal("5.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    service = _build_service(db_session)

    inventory = service.get_inventory(company.id, product.id)
    assert inventory.current_stock == Decimal("10.00")
    assert inventory.stock_value == Decimal("8000.00")
    assert inventory.low_stock is False

    updated = service.create_inventory_transaction(
        company.id,
        product.id,
        actor,
        ProductInventoryTransactionCreateRequest(transaction_type="stock_out", quantity=Decimal("3")),
    )
    assert updated.current_stock == Decimal("7.00")

    history = service.list_inventory_history(company.id, product.id)
    assert len(history) == 1
    assert history[0].quantity_after == Decimal("7.00")


def test_product_service_category_tree(db_session) -> None:
    company, _ = _create_company_and_user(db_session)
    service = _build_service(db_session)

    parent = service.create_category(
        company.id,
        ProductCategoryCreateRequest(name="Plumbing", slug="plumbing", sort_order=1),
    )
    child = service.create_category(
        company.id,
        ProductCategoryCreateRequest(name="Pipes", slug="pipes", parent_id=parent.id, sort_order=2),
    )

    db_session.add(
        Product(
            company_id=company.id,
            category_id=child.id,
            category="Pipes",
            name="PVC Pipe 20",
            unit="pcs",
            currency="KZT",
            price=Decimal("1250.00"),
            is_active=True,
        )
    )
    db_session.commit()

    categories = service.list_categories(company.id)
    assert categories.items[0].slug == "plumbing"
    assert categories.items[0].children[0].slug == "pipes"
    assert categories.items[0].children[0].product_count == 1
