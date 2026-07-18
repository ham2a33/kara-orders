from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.inventory_transaction import InventoryTransaction
from app.repositories.base import CompanyScopedRepository


class InventoryTransactionRepository(CompanyScopedRepository[InventoryTransaction]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=InventoryTransaction)

    def list_for_product(self, company_id, product_id) -> list[InventoryTransaction]:
        statement = select(InventoryTransaction).where(
            InventoryTransaction.company_id == company_id,
            InventoryTransaction.product_id == product_id,
        ).order_by(InventoryTransaction.created_at.desc())
        return list(self.session.scalars(statement).all())

