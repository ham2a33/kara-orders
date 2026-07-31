from __future__ import annotations

from typing import Literal

OrderStatus = Literal["draft", "new", "confirmed", "deleted"]

ORDER_STATUS_DRAFT: OrderStatus = "draft"
ORDER_STATUS_NEW: OrderStatus = "new"
ORDER_STATUS_CONFIRMED: OrderStatus = "confirmed"
ORDER_STATUS_DELETED: OrderStatus = "deleted"

ORDER_STATUSES: tuple[OrderStatus, ...] = (
    ORDER_STATUS_DRAFT,
    ORDER_STATUS_NEW,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_DELETED,
)
