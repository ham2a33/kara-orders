from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


AnalyticsPreset = Literal["today", "yesterday", "last_7_days", "last_30_days", "this_month", "last_month"]
AnalyticsExportFormat = Literal["csv", "excel", "pdf"]
AnalyticsGranularity = Literal["day", "month"]


class AnalyticsRangeRead(BaseModel):
    preset: AnalyticsPreset
    start_date: date
    end_date: date
    timezone: str


class AnalyticsSeriesPointRead(BaseModel):
    label: str
    value: Decimal
    count: int = 0


class DashboardMetricsRead(BaseModel):
    today_revenue: Decimal
    week_revenue: Decimal
    month_revenue: Decimal
    today_orders: int
    week_orders: int
    month_orders: int
    average_invoice: Decimal
    total_products: int
    low_stock_products: int
    out_of_stock_products: int


class AnalyticsStatusBreakdownRead(BaseModel):
    new_orders: int
    confirmed_orders: int
    deleted_orders: int
    average_order_value: Decimal
    largest_order: Decimal


class InventorySummaryRead(BaseModel):
    total_products: int
    low_stock_products: int
    out_of_stock_products: int
    inventory_value: Decimal


class AnalyticsTopProductRead(BaseModel):
    product_id: UUID | None = None
    product_name: str
    sku: str | None = None
    unit: str | None = None
    quantity_sold: Decimal
    revenue: Decimal
    order_count: int


class AnalyticsTopCategoryRead(BaseModel):
    category_name: str
    quantity_sold: Decimal
    revenue: Decimal
    product_count: int


class AnalyticsTopCustomerRead(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    order_count: int
    revenue: Decimal
    last_order_at: datetime


class AnalyticsRecentOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    customer_name: str | None = None
    customer_phone: str | None = None
    status: str
    total: Decimal
    created_at: datetime


class DashboardResponse(BaseModel):
    range: AnalyticsRangeRead
    metrics: DashboardMetricsRead
    revenue_by_day: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    orders_by_day: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    top_products: list[AnalyticsTopProductRead] = Field(default_factory=list)
    top_categories: list[AnalyticsTopCategoryRead] = Field(default_factory=list)
    top_customers: list[AnalyticsTopCustomerRead] = Field(default_factory=list)
    recent_orders: list[AnalyticsRecentOrderRead] = Field(default_factory=list)
    inventory_summary: InventorySummaryRead


class RevenueAnalyticsResponse(BaseModel):
    range: AnalyticsRangeRead
    daily: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    monthly: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    metrics: DashboardMetricsRead


class OrdersAnalyticsResponse(BaseModel):
    range: AnalyticsRangeRead
    daily: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    monthly: list[AnalyticsSeriesPointRead] = Field(default_factory=list)
    status_breakdown: AnalyticsStatusBreakdownRead
    recent_orders: list[AnalyticsRecentOrderRead] = Field(default_factory=list)


class ProductsAnalyticsResponse(BaseModel):
    range: AnalyticsRangeRead
    top_products: list[AnalyticsTopProductRead] = Field(default_factory=list)
    top_categories: list[AnalyticsTopCategoryRead] = Field(default_factory=list)
    inventory_summary: InventorySummaryRead


class CustomersAnalyticsResponse(BaseModel):
    range: AnalyticsRangeRead
    top_customers: list[AnalyticsTopCustomerRead] = Field(default_factory=list)
    recent_orders: list[AnalyticsRecentOrderRead] = Field(default_factory=list)


class AnalyticsExportRequest(BaseModel):
    format: AnalyticsExportFormat = "csv"
    preset: AnalyticsPreset = "last_30_days"
    start_date: date | None = None
    end_date: date | None = None
