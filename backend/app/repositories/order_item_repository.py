from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.order_item import OrderItem
from app.repositories.base import BaseRepository


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, session: Session) -> None:
        super().__init__(session=session, model=OrderItem)

    def list_for_order(self, order_id) -> list[OrderItem]:
        statement = select(OrderItem).where(OrderItem.order_id == order_id)
        return list(self.session.scalars(statement).all())
