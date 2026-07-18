from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.product_image import ProductImage
from app.repositories.base import CompanyScopedRepository


class ProductImageRepository(CompanyScopedRepository[ProductImage]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=ProductImage)
