from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.db.models.company import Company
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.services.invoice_service import InvoiceService


def test_invoice_service_generates_russian_receipt_pdf() -> None:
    company = Company(
        name="Kara Build",
        currency="KZT",
        invoice_prefix="INV",
        bin_tax_id="123456789012",
        phone="+7 777 123-45-67",
        email="info@kara.kz",
        website="www.kara.kz",
        address="г. Алматы, ул. Абая 10",
        tax_percentage=Decimal("12"),
        timezone="Asia/Almaty",
    )
    order = Order(
        company_id=uuid4(),
        invoice_number="000123",
        customer_name="Иван Иванов",
        input_method="manual",
        status="new",
        subtotal=Decimal("1700.00"),
        discount_total=Decimal("0"),
        tax_total=Decimal("204.00"),
        total=Decimal("1904.00"),
        created_by=uuid4(),
        created_at=datetime(2026, 7, 30, 9, 53, tzinfo=timezone.utc),
    )
    order.company = company
    order.items = [
        OrderItem(
            order_id=order.id,
            product_name="Труба PVC 20 мм",
            quantity=Decimal("2"),
            unit_price=Decimal("850.00"),
            discount_amount=Decimal("0"),
            tax_amount=Decimal("204.00"),
            line_total=Decimal("1700.00"),
        )
    ]

    pdf = InvoiceService().generate_pdf(company, order)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
