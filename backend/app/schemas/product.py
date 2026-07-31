from typing import Literal
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    url: str
    storage_path: str | None = None
    alt_text: str | None = None
    sort_order: int
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ProductTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    color: str | None = None
    is_active: bool


class ProductCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    product_count: int = 0
    children: list["ProductCategoryRead"] = Field(default_factory=list)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    category_id: UUID | None = None
    name: str
    description: str | None = None
    size: str | None = None
    manufacturer: str | None = None
    sku: str | None = None
    barcode: str | None = None
    aliases: list[str] = Field(default_factory=list)
    category: str | None = None
    unit: str
    currency: str
    price: Decimal
    cost: Decimal | None = None
    tax_rate: Decimal | None = None
    stock_qty: Decimal | None = None
    low_stock_threshold: Decimal | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    stock_value: Decimal = Decimal("0")
    low_stock: bool = False
    tags: list[ProductTagRead] = Field(default_factory=list)
    images: list[ProductImageRead] = Field(default_factory=list)
    category_rel: ProductCategoryRead | None = None


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    size: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    manufacturer: str | None = Field(default=None, max_length=120)
    sku: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    aliases: list[str] = Field(default_factory=list)
    category_id: UUID | None = None
    category: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="pcs", min_length=1, max_length=32)
    currency: str = Field(default="KZT", min_length=3, max_length=3)
    price: Decimal = Field(ge=0)
    cost: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    stock_qty: Decimal | None = Field(default=None, ge=0)
    low_stock_threshold: Decimal | None = Field(default=None, ge=0)
    is_active: bool = True
    tag_ids: list[UUID] = Field(default_factory=list)


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    size: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    manufacturer: str | None = Field(default=None, max_length=120)
    sku: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    aliases: list[str] | None = None
    category_id: UUID | None = None
    category: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price: Decimal | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    stock_qty: Decimal | None = Field(default=None, ge=0)
    low_stock_threshold: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    tag_ids: list[UUID] | None = None


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    page: int
    page_size: int
    total: int


class ProductRestoreResponse(BaseModel):
    detail: str


class ProductInventoryTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    transaction_type: str
    quantity: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    unit_cost: Decimal | None = None
    note: str | None = None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


class ProductInventoryTransactionCreateRequest(BaseModel):
    transaction_type: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)


class ProductInventoryResponse(BaseModel):
    current_stock: Decimal
    stock_value: Decimal
    low_stock: bool


class ProductTagCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=100)
    color: str | None = Field(default=None, max_length=32)


class ProductTagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    color: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None


class ProductCategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=140)
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int = 0


class ProductCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=140)
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ProductTagListResponse(BaseModel):
    items: list[ProductTagRead]


class ProductCategoryListResponse(BaseModel):
    items: list[ProductCategoryRead]


class ProductBulkIdsRequest(BaseModel):
    product_ids: list[UUID] = Field(min_length=1, max_length=5000)


class ProductBulkPriceUpdateRequest(ProductBulkIdsRequest):
    field: Literal["price", "cost"] = "price"
    operation: Literal["increase", "decrease"] = "increase"
    mode: Literal["percentage", "fixed"] = "percentage"
    value: Decimal = Field(gt=0)


class ProductBulkVatUpdateRequest(ProductBulkIdsRequest):
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)


class ProductBulkStatusUpdateRequest(ProductBulkIdsRequest):
    is_active: bool


class ProductBulkActionResponse(BaseModel):
    updated: int
    product_ids: list[UUID]
