from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.core.order_statuses import OrderStatus
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.deps import get_app_settings, get_db
from app.db.models.user import User
from app.schemas.order import (
    InvoicePreviewResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderRead,
    OrderRestoreResponse,
    OrderUpdateRequest,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def _service(session: Session, settings: Settings) -> OrderService:
    return OrderService(session=session, settings=settings)


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: OrderStatus | None = None,
    include_deleted: bool = False,
    sort_by: Literal["created_at", "updated_at", "invoice_number", "customer_name", "status", "total"] = "created_at",
    sort_dir: Literal["asc", "desc"] = "desc",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderListResponse:
    return _service(session, settings).list_orders(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        include_deleted=include_deleted,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post("", response_model=OrderRead, status_code=201)
def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderRead:
    return _service(session, settings).create_order(current_user.company_id, current_user, payload)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderRead:
    return _service(session, settings).get_order(current_user.company_id, order_id)


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: UUID,
    payload: OrderUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderRead:
    return _service(session, settings).update_order(current_user.company_id, order_id, payload)


@router.delete("/{order_id}", response_model=OrderRestoreResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN))])
def delete_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderRestoreResponse:
    _service(session, settings).delete_order(current_user.company_id, order_id)
    return OrderRestoreResponse(detail="Order deleted")


@router.post("/{order_id}/restore", response_model=OrderRestoreResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN))])
def restore_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrderRestoreResponse:
    return _service(session, settings).restore_order(current_user.company_id, order_id)


@router.get("/{order_id}/invoice/preview", response_model=InvoicePreviewResponse)
def preview_invoice(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> InvoicePreviewResponse:
    return _service(session, settings).preview_invoice(current_user.company_id, order_id)


@router.get("/{order_id}/invoice/pdf")
def download_invoice_pdf(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    return _service(session, settings).generate_invoice_pdf(current_user.company_id, order_id)
