from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from starlette.responses import StreamingResponse

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.models.company import Company
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.product import Product
from app.db.models.user import User
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    InvoicePreviewResponse,
    OrderCreateRequest,
    OrderItemRead,
    OrderItemWrite,
    OrderListResponse,
    OrderRead,
    OrderRestoreResponse,
    OrderUpdateRequest,
)
from app.services.invoice_service import InvoiceService
from app.services.platform_service import PlatformService


@dataclass(frozen=True)
class OrderTotals:
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


class OrderService:
    _SORT_COLUMNS = {
        "created_at": Order.created_at,
        "updated_at": Order.updated_at,
        "invoice_number": Order.invoice_number,
        "customer_name": Order.customer_name,
        "status": Order.status,
        "total": Order.total,
    }

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.orders = OrderRepository(session)
        self.invoice_service = InvoiceService()

    def list_orders(
        self,
        company_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> OrderListResponse:
        sort_column = self._SORT_COLUMNS.get(sort_by, Order.created_at)
        sort_expression = sort_column.asc() if sort_dir.lower() == "asc" else sort_column.desc()
        statement = (
            select(Order)
            .where(Order.company_id == company_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )
        if not include_deleted:
            statement = statement.where(Order.deleted_at.is_(None))
        if status:
            statement = statement.where(Order.status == status)
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Order.invoice_number.ilike(term),
                    Order.customer_name.ilike(term),
                    Order.customer_phone.ilike(term),
                    Order.customer_address.ilike(term),
                )
            )

        statement = statement.order_by(sort_expression)
        total = int(self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        orders = list(self.session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all())
        return OrderListResponse(
            items=[self._serialize_order(order) for order in orders],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_order(self, company_id: UUID, order_id: UUID) -> OrderRead:
        order = self.orders.get_with_items(order_id, company_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("Order not found")
        return self._serialize_order(order)

    def create_order(self, company_id: UUID, current_user: User, payload: OrderCreateRequest) -> OrderRead:
        self._validate_status(payload.status)
        platform = PlatformService(self.session)
        platform.ensure_limit(
            company_id,
            "maximum_orders_per_month",
            1,
            message="Order limit reached",
        )
        company = self._get_company_for_update(company_id)
        invoice_number = self._build_invoice_number(company)
        order = Order(
            company_id=company_id,
            invoice_number=invoice_number,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            notes=payload.notes,
            input_method="manual",
            status=payload.status,
            subtotal=Decimal("0"),
            discount_total=Decimal("0"),
            tax_total=Decimal("0"),
            total=Decimal("0"),
            created_by=current_user.id,
        )
        self.session.add(order)
        self.session.flush()
        items, totals = self._build_items(company_id, order, payload.items, company.tax_percentage)
        order.items[:] = items
        order.subtotal = totals.subtotal
        order.discount_total = totals.discount_total
        order.tax_total = totals.tax_total
        order.total = totals.total
        self.session.commit()
        self.session.refresh(order)
        platform.log_action(
            action="order_created",
            company_id=company_id,
            actor_user_id=current_user.id,
            resource_type="order",
            resource_id=str(order.id),
            description="Order created",
            metadata={"status": payload.status, "items": len(payload.items)},
        )
        return self.get_order(company_id, order.id)

    def update_order(self, company_id: UUID, order_id: UUID, payload: OrderUpdateRequest) -> OrderRead:
        order = self._get_order_or_404(company_id, order_id)
        if payload.status is not None:
            self._validate_status(payload.status)
            order.status = payload.status
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field in {"items", "status"}:
                continue
            setattr(order, field, value)

        if payload.items is not None:
            company_tax = self._get_company_tax(company_id)
            items, totals = self._build_items(company_id, order, payload.items, company_tax)
            order.items[:] = items
            order.subtotal = totals.subtotal
            order.discount_total = totals.discount_total
            order.tax_total = totals.tax_total
            order.total = totals.total

        self.session.commit()
        self.session.refresh(order)
        PlatformService(self.session).log_action(
            action="order_updated",
            company_id=company_id,
            actor_user_id=None,
            resource_type="order",
            resource_id=str(order.id),
            description="Order updated",
            metadata=payload.model_dump(exclude_unset=True),
        )
        return self.get_order(company_id, order.id)

    def delete_order(self, company_id: UUID, order_id: UUID) -> None:
        order = self._get_order_or_404(company_id, order_id)
        order.deleted_at = sa.func.now()
        order.status = "cancelled"
        self.session.commit()
        PlatformService(self.session).log_action(
            action="order_deleted",
            company_id=company_id,
            actor_user_id=None,
            resource_type="order",
            resource_id=str(order.id),
            description="Order soft deleted",
        )

    def restore_order(self, company_id: UUID, order_id: UUID) -> OrderRestoreResponse:
        order = self._get_order_or_404(company_id, order_id, include_deleted=True)
        order.deleted_at = None
        self.session.commit()
        PlatformService(self.session).log_action(
            action="order_restored",
            company_id=company_id,
            actor_user_id=None,
            resource_type="order",
            resource_id=str(order.id),
            description="Order restored",
        )
        return OrderRestoreResponse(detail="Order restored")

    def preview_invoice(self, company_id: UUID, order_id: UUID) -> InvoicePreviewResponse:
        order = self.orders.get_with_items(order_id, company_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("Order not found")
        return InvoicePreviewResponse(order=self._serialize_order(order), company_name=order.company.name)

    def generate_invoice_pdf(self, company_id: UUID, order_id: UUID) -> StreamingResponse:
        order = self.orders.get_with_items(order_id, company_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("Order not found")
        pdf_bytes = self.invoice_service.generate_pdf(order.company, order)
        filename = f"invoice-{order.invoice_number}.pdf"
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def _get_order_or_404(self, company_id: UUID, order_id: UUID, include_deleted: bool = False) -> Order:
        statement = select(Order).where(Order.company_id == company_id, Order.id == order_id)
        if not include_deleted:
            statement = statement.where(Order.deleted_at.is_(None))
        order = self.session.scalar(statement.options(selectinload(Order.items).selectinload(OrderItem.product)))
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def _build_invoice_number(self, company: Company) -> str:
        invoice_number = company.invoice_number_format.format(
            prefix=company.invoice_prefix,
            number=company.next_invoice_number,
        )
        company.next_invoice_number += 1
        return invoice_number

    def _get_company_for_update(self, company_id: UUID) -> Company:
        statement = select(Company).where(Company.id == company_id).with_for_update()
        company = self.session.scalar(statement)
        if company is None or company.deleted_at is not None:
            raise NotFoundError("Company not found")
        return company

    def _build_items(
        self,
        company_id: UUID,
        order: Order,
        payload_items: list[OrderItemWrite],
        company_tax_percentage: Decimal,
    ) -> tuple[list[OrderItem], OrderTotals]:
        if not payload_items:
            raise ValidationAppError("Orders must contain at least one item")

        product_ids = [item.product_id for item in payload_items]
        products = self.session.scalars(
            select(Product).where(
                Product.company_id == company_id,
                Product.id.in_(product_ids),
                Product.deleted_at.is_(None),
            )
        ).all()
        products_by_id = {product.id: product for product in products}
        if len(products_by_id) != len(set(product_ids)):
            raise NotFoundError("One or more products were not found")

        created_items: list[OrderItem] = []
        subtotal = Decimal("0")
        discount_total = Decimal("0")
        tax_total = Decimal("0")

        for item_payload in payload_items:
            product = products_by_id[item_payload.product_id]
            quantity = self._quantize(item_payload.quantity)
            unit_price = self._quantize(Decimal(str(product.price)))
            line_subtotal = self._quantize(quantity * unit_price)
            discount_amount = self._quantize(item_payload.discount_amount or Decimal("0"))
            if discount_amount > line_subtotal:
                raise ValidationAppError("Discount cannot exceed line subtotal")
            taxable_base = line_subtotal - discount_amount
            tax_amount = self._quantize(taxable_base * Decimal(str(company_tax_percentage)) / Decimal("100"))
            line_total = self._quantize(taxable_base + tax_amount)

            created_items.append(
                OrderItem(
                    order=order,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_amount=discount_amount,
                    tax_amount=tax_amount,
                    line_total=line_total,
                )
            )
            subtotal += line_subtotal
            discount_total += discount_amount
            tax_total += tax_amount

        total = subtotal - discount_total + tax_total
        return created_items, OrderTotals(
            subtotal=self._quantize(subtotal),
            discount_total=self._quantize(discount_total),
            tax_total=self._quantize(tax_total),
            total=self._quantize(total),
        )

    def _get_company_tax(self, company_id: UUID) -> Decimal:
        company = self.session.scalar(select(Company.tax_percentage).where(Company.id == company_id))
        if company is None:
            raise NotFoundError("Company not found")
        return Decimal(str(company))

    def _serialize_order(self, order: Order) -> OrderRead:
        return OrderRead(
            id=order.id,
            company_id=order.company_id,
            invoice_number=order.invoice_number,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_address=order.customer_address,
            notes=order.notes,
            input_method=order.input_method,
            status=order.status,
            subtotal=order.subtotal,
            discount_total=order.discount_total,
            tax_total=order.tax_total,
            total=order.total,
            created_by=order.created_by,
            created_at=order.created_at,
            updated_at=order.updated_at,
            deleted_at=order.deleted_at,
            items=[self._serialize_item(item) for item in order.items],
        )

    def _serialize_item(self, item: OrderItem) -> OrderItemRead:
        return OrderItemRead(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount,
            tax_amount=item.tax_amount,
            line_total=item.line_total,
            ai_confidence=item.ai_confidence,
            product=item.product if item.product is not None else None,
        )

    def _validate_status(self, status: str) -> None:
        if status not in {"draft", "confirmed", "completed", "cancelled"}:
            raise ValidationAppError("Invalid order status")

    def _quantize(self, value: Decimal) -> Decimal:
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
