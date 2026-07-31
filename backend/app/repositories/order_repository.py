from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.repositories.base import CompanyScopedRepository


class OrderRepository(CompanyScopedRepository[Order]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=Order)

    def get_with_items(self, order_id, company_id) -> Order | None:
        statement = (
            select(Order)
            .where(Order.id == order_id, Order.company_id == company_id)
            .options(selectinload(Order.company), selectinload(Order.items).selectinload(OrderItem.product))
        )
        return self.session.scalar(statement)

    def get_by_invoice_number(self, company_id, invoice_number: str) -> Order | None:
        statement = select(Order).where(
            Order.company_id == company_id,
            Order.invoice_number == invoice_number,
        )
        return self.session.scalar(statement)
