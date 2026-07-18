from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.core.auth import Role
from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.order import OrderCreateRequest, OrderItemWrite
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService


def _create_company(db_session, *, tax_percentage: Decimal = Decimal("12.00")) -> Company:
    company = Company(
        name=f"Acme {uuid4().hex[:6]}",
        currency="KZT",
        invoice_prefix="INV",
        tax_percentage=tax_percentage,
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


def _create_owner(db_session, company: Company) -> User:
    user = User(
        company_id=company.id,
        email=f"owner-{uuid4().hex[:6]}@acme.example.com",
        password_hash=hash_password("Password123!"),
        full_name="Owner",
        role=Role.OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_order_service_calculates_totals(db_session) -> None:
    company = _create_company(db_session)
    owner = _create_owner(db_session, company)
    product = Product(
        company_id=company.id,
        name="PVC Pipe 20",
        sku="PIP-020",
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        cost=Decimal("70.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    service = OrderService(db_session, Settings(database_url="postgresql+psycopg://example"))
    order = service.create_order(
        company.id,
        owner,
        OrderCreateRequest(
            customer_name="Khan Market",
            customer_phone="+7 700 000 00 00",
            customer_address="Almaty",
            notes="Deliver quickly",
            items=[OrderItemWrite(product_id=product.id, quantity=Decimal("2"), discount_amount=Decimal("10"))],
        ),
    )

    assert order.subtotal == Decimal("200.00")
    assert order.discount_total == Decimal("10.00")
    assert order.tax_total == Decimal("22.80")
    assert order.total == Decimal("212.80")
    assert order.items[0].line_total == Decimal("212.80")


def test_invoice_service_generates_pdf_bytes(db_session) -> None:
    company = _create_company(db_session)
    owner = _create_owner(db_session, company)
    product = Product(
        company_id=company.id,
        name="Valve 1/2",
        sku="VAL-050",
        unit="pcs",
        currency="KZT",
        price=Decimal("4900.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    order = Order(
        company_id=company.id,
        invoice_number="INV-000001",
        customer_name="Auto Pro",
        customer_phone="+7 700 111 22 33",
        customer_address="Astana",
        notes="Handle with care",
        input_method="manual",
        status="draft",
        subtotal=Decimal("4900.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("588.00"),
        total=Decimal("5488.00"),
        created_by=owner.id,
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=Decimal("1.00"),
            unit_price=Decimal("4900.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("588.00"),
            line_total=Decimal("5488.00"),
        )
    )
    db_session.commit()
    db_session.refresh(order)

    pdf_bytes = InvoiceService().generate_pdf(company, order)
    assert pdf_bytes.startswith(b"%PDF")
