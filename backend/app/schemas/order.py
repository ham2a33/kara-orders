from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.order_statuses import OrderStatus, ORDER_STATUS_NEW
from app.schemas.product import ProductRead


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    product_id: UUID | None = None
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal
    ai_confidence: Decimal | None = None
    product: ProductRead | None = None


class OrderItemWrite(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    discount_amount: Decimal | None = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


class OrderCreateRequest(BaseModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=32)
    customer_address: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    status: OrderStatus = ORDER_STATUS_NEW
    items: list[OrderItemWrite] = Field(min_length=1)


class OrderUpdateRequest(BaseModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=32)
    customer_address: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)
    status: OrderStatus | None = None
    items: list[OrderItemWrite] | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    invoice_number: str
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_address: str | None = None
    notes: str | None = None
    input_method: str
    status: OrderStatus
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    items: list[OrderItemRead] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    items: list[OrderRead]
    page: int
    page_size: int
    total: int


class OrderRestoreResponse(BaseModel):
    detail: str


class InvoicePdfResponse(BaseModel):
    filename: str
    content_type: str = "application/pdf"


class InvoicePreviewResponse(BaseModel):
    order: OrderRead
    company_name: str
    company: "InvoiceCompanyPreview"
    pdf_url: str | None = None


class InvoiceCompanyPreview(BaseModel):
    name: str
    bin_tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    instagram: str | None = None
    director_name: str | None = None
    welcome_message: str | None = None
    receipt_signature: str | None = None
    footer_text: str | None = None
    invoice_logo_url: str | None = None
    tax_percentage: Decimal
    currency: str
    timezone: str = "Asia/Almaty"
