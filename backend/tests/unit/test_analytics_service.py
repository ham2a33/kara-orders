from __future__ import annotations

from datetime import datetime, timezone
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
from app.services.analytics_service import AnalyticsService


def _create_company(db_session) -> Company:
    company = Company(
        name=f"Analytics Co {uuid4().hex[:6]}",
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
        email=f"owner-{uuid4().hex[:6]}@analytics.example.com",
        password_hash=hash_password("Password123!"),
        full_name="Owner",
        role=Role.OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_product(db_session, company: Company, *, name: str, sku: str, stock_qty: Decimal, threshold: Decimal) -> Product:
    product = Product(
        company_id=company.id,
        name=name,
        sku=sku,
        unit="pcs",
        currency="KZT",
        price=Decimal("100.00"),
        cost=Decimal("60.00"),
        stock_qty=stock_qty,
        low_stock_threshold=threshold,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def _create_order(
    db_session,
    company: Company,
    user: User,
    *,
    invoice_number: str,
    status: str,
    total: Decimal,
    customer_name: str,
    product: Product,
    quantity: Decimal,
) -> Order:
    order = Order(
        company_id=company.id,
        invoice_number=invoice_number,
        customer_name=customer_name,
        customer_phone="+7 700 000 00 00",
        customer_address="Almaty",
        input_method="manual",
        status=status,
        subtotal=total,
        discount_total=Decimal("0"),
        tax_total=Decimal("0"),
        total=total,
        created_by=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    order.items = [
        OrderItem(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0"),
            tax_amount=Decimal("0"),
            line_total=total,
        )
    ]
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


def test_analytics_service_dashboard_and_exports(db_session) -> None:
    company = _create_company(db_session)
    owner = _create_owner(db_session, company)
    product_one = _create_product(db_session, company, name="Valve 1/2", sku="VAL-050", stock_qty=Decimal("12"), threshold=Decimal("5"))
    product_two = _create_product(db_session, company, name="Pipe 20", sku="PIP-020", stock_qty=Decimal("0"), threshold=Decimal("4"))

    _create_order(
        db_session,
        company,
        owner,
        invoice_number="INV-000001",
        status="completed",
        total=Decimal("150.00"),
        customer_name="Khan Market",
        product=product_one,
        quantity=Decimal("2"),
    )
    _create_order(
        db_session,
        company,
        owner,
        invoice_number="INV-000002",
        status="completed",
        total=Decimal("90.00"),
        customer_name="Metro Store",
        product=product_one,
        quantity=Decimal("1"),
    )
    _create_order(
        db_session,
        company,
        owner,
        invoice_number="INV-000003",
        status="draft",
        total=Decimal("45.00"),
        customer_name="Draft Customer",
        product=product_two,
        quantity=Decimal("1"),
    )

    service = AnalyticsService(db_session, Settings(database_url="postgresql+psycopg://example", secret_key="secret"))
    dashboard = service.get_dashboard(company.id)

    assert dashboard.metrics.total_products == 2
    assert dashboard.metrics.out_of_stock_products == 1
    assert dashboard.metrics.low_stock_products == 0
    assert dashboard.metrics.month_revenue == Decimal("240.00")
    assert dashboard.metrics.average_invoice == Decimal("120.00")
    assert dashboard.top_products[0].product_name == "Valve 1/2"
    assert dashboard.top_customers[0].customer_name == "Khan Market"

    revenue = service.get_revenue_analytics(company.id)
    assert revenue.daily
    orders = service.get_orders_analytics(company.id)
    assert orders.status_breakdown.completed_orders == 2
    products = service.get_products_analytics(company.id)
    assert products.inventory_summary.total_products == 2
    customers = service.get_customers_analytics(company.id)
    assert customers.top_customers[0].order_count == 1

    csv_bytes, csv_type, csv_name = service.export_analytics(company.id, export_format="csv")
    assert csv_type == "text/csv; charset=utf-8"
    assert csv_name == "analytics.csv"
    assert csv_bytes.startswith(b"Kara Orders Analytics Export")

    xlsx_bytes, xlsx_type, xlsx_name = service.export_analytics(company.id, export_format="excel")
    assert xlsx_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert xlsx_name == "analytics.xlsx"
    assert xlsx_bytes[:2] == b"PK"

    pdf_bytes, pdf_type, pdf_name = service.export_analytics(company.id, export_format="pdf")
    assert pdf_type == "application/pdf"
    assert pdf_name == "analytics.pdf"
    assert pdf_bytes.startswith(b"%PDF")

