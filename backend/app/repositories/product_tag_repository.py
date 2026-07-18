from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.product_tag import ProductTag
from app.repositories.base import CompanyScopedRepository


class ProductTagRepository(CompanyScopedRepository[ProductTag]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=ProductTag)

    def get_by_slug(self, company_id, slug: str) -> ProductTag | None:
        statement = select(ProductTag).where(
            ProductTag.company_id == company_id,
            ProductTag.slug == slug,
            ProductTag.deleted_at.is_(None),
        )
        return self.session.scalar(statement)

