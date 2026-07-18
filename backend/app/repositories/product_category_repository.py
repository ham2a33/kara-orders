from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.product_category import ProductCategory
from app.repositories.base import CompanyScopedRepository


class ProductCategoryRepository(CompanyScopedRepository[ProductCategory]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=ProductCategory)

    def get_by_slug(self, company_id, slug: str) -> ProductCategory | None:
        statement = select(ProductCategory).where(
            ProductCategory.company_id == company_id,
            ProductCategory.slug == slug,
            ProductCategory.deleted_at.is_(None),
        )
        return self.session.scalar(statement)

