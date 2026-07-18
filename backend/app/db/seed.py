from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.product import Product
from app.db.models.user import User
from app.db.session import SessionLocal

DEV_COMPANY_NAME = "Kara Demo Supplies"
DEV_OWNER_EMAIL = "owner@kara-orders.example"
DEV_OWNER_PASSWORD = "Password123!"
DEV_ADMIN_EMAIL = "admin@kara-orders.example"
DEV_ADMIN_PASSWORD = "Admin123!Password"
DEV_MANAGER_EMAIL = "manager@kara-orders.example"
DEV_MANAGER_PASSWORD = "Manager123!Password"
DEV_EMPLOYEE_EMAIL = "employee@kara-orders.example"
DEV_EMPLOYEE_PASSWORD = "Employee123!Password"


def seed_development_data() -> None:
    with SessionLocal() as session:
        company = session.scalar(select(Company).where(Company.name == DEV_COMPANY_NAME))
        if company is None:
            company = Company(
                name=DEV_COMPANY_NAME,
                currency="KZT",
                invoice_prefix="INV",
                address="Almaty",
                phone="+7 700 000 00 00",
            )
            session.add(company)
            session.flush()

        owner = session.scalar(select(User).where(User.email == DEV_OWNER_EMAIL))
        if owner is None:
            owner = User(
                company_id=company.id,
                email=DEV_OWNER_EMAIL,
                password_hash=hash_password(DEV_OWNER_PASSWORD),
                full_name="Demo Owner",
                role="owner",
                is_active=True,
            )
            session.add(owner)

        additional_users = [
            (DEV_ADMIN_EMAIL, DEV_ADMIN_PASSWORD, "admin", "Demo Admin"),
            (DEV_MANAGER_EMAIL, DEV_MANAGER_PASSWORD, "manager", "Demo Manager"),
            (DEV_EMPLOYEE_EMAIL, DEV_EMPLOYEE_PASSWORD, "employee", "Demo Employee"),
        ]

        for email, password, role, full_name in additional_users:
            existing_user = session.scalar(select(User).where(User.email == email))
            if existing_user is None:
                session.add(
                    User(
                        company_id=company.id,
                        email=email,
                        password_hash=hash_password(password),
                        full_name=full_name,
                        role=role,
                        is_active=True,
                    )
                )

        products = [
            {
                "name": "Pipe 20mm PVC",
                "sku": "PIPE-20-PVC",
                "category": "Plumbing",
                "unit": "m",
                "price": Decimal("1200.00"),
                "cost": Decimal("800.00"),
                "stock_qty": Decimal("250.00"),
            },
            {
                "name": "Ball Valve 1/2\"",
                "sku": "VALVE-12",
                "category": "Plumbing",
                "unit": "pcs",
                "price": Decimal("4500.00"),
                "cost": Decimal("3100.00"),
                "stock_qty": Decimal("80.00"),
            },
            {
                "name": "Copper Cable 2x1.5",
                "sku": "CABLE-2X15",
                "category": "Electrical",
                "unit": "m",
                "price": Decimal("980.00"),
                "cost": Decimal("650.00"),
                "stock_qty": Decimal("500.00"),
            },
            {
                "name": "Anchor Bolt M8",
                "sku": "BOLT-M8",
                "category": "Hardware",
                "unit": "pcs",
                "price": Decimal("65.00"),
                "cost": Decimal("30.00"),
                "stock_qty": Decimal("1500.00"),
            },
        ]

        for product_data in products:
            product = session.scalar(
                select(Product).where(
                    Product.company_id == company.id,
                    Product.sku == product_data["sku"],
                )
            )
            if product is None:
                session.add(Product(company_id=company.id, **product_data))

        session.commit()


if __name__ == "__main__":
    seed_development_data()
