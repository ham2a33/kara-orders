from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.product import Product
from app.repositories.base import CompanyScopedRepository


class ProductRepository(CompanyScopedRepository[Product]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=Product)

    def get_by_sku(self, company_id, sku: str) -> Product | None:
        statement = select(Product).where(
            Product.company_id == company_id,
            Product.sku == sku,
            Product.deleted_at.is_(None),
        )
        return self.session.scalar(statement)

    def get_by_barcode(self, company_id, barcode: str) -> Product | None:
        statement = select(Product).where(
            Product.company_id == company_id,
            Product.barcode == barcode,
            Product.deleted_at.is_(None),
        )
        return self.session.scalar(statement)

    def get_with_relations(self, product_id, company_id) -> Product | None:
        statement = (
            select(Product)
            .where(Product.id == product_id, Product.company_id == company_id)
            .options(selectinload(Product.tags), selectinload(Product.images), selectinload(Product.category_rel))
        )
        return self.session.scalar(statement)

    def list_query(self, company_id):
        return select(Product).where(Product.company_id == company_id)
