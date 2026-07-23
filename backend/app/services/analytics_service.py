from __future__ import annotations

import csv
import io
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, time as time_obj, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
from uuid import UUID

import sqlalchemy as sa
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session
from xlsxwriter import Workbook

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.order_statuses import ORDER_STATUS_CONFIRMED, ORDER_STATUS_DELETED, ORDER_STATUS_NEW
from app.db.models.company import Company
from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.product import Product
from app.db.models.product_category import ProductCategory
from app.schemas.analytics import (
    AnalyticsExportFormat,
    AnalyticsPreset,
    AnalyticsRangeRead,
    AnalyticsRecentOrderRead,
    AnalyticsSeriesPointRead,
    AnalyticsStatusBreakdownRead,
    AnalyticsTopCategoryRead,
    AnalyticsTopCustomerRead,
    AnalyticsTopProductRead,
    CustomersAnalyticsResponse,
    DashboardMetricsRead,
    DashboardResponse,
    InventorySummaryRead,
    OrdersAnalyticsResponse,
    ProductsAnalyticsResponse,
    RevenueAnalyticsResponse,
)


@dataclass(frozen=True)
class AnalyticsWindow:
    preset: AnalyticsPreset
    timezone: str
    start_at: datetime
    end_at: datetime
    start_date: date
    end_date: date


_CACHE_LOCK = threading.Lock()
_ANALYTICS_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL_SECONDS = 60.0


class AnalyticsService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def get_dashboard(
        self,
        company_id: UUID,
        *,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> DashboardResponse:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        cache_key = self._cache_key("dashboard", company_id, window)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return DashboardResponse.model_validate(cached)

        payload = self._build_dashboard(company_id, company, window)
        self._cache_set(cache_key, payload.model_dump(mode="json"))
        return payload

    def get_revenue_analytics(
        self,
        company_id: UUID,
        *,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> RevenueAnalyticsResponse:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        cache_key = self._cache_key("revenue", company_id, window)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return RevenueAnalyticsResponse.model_validate(cached)

        payload = RevenueAnalyticsResponse(
            range=self._window_read(window),
            daily=self._daily_revenue(company_id, window),
            monthly=self._monthly_revenue(company_id, window),
            metrics=self._dashboard_metrics(company_id, company, window),
        )
        self._cache_set(cache_key, payload.model_dump(mode="json"))
        return payload

    def get_orders_analytics(
        self,
        company_id: UUID,
        *,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> OrdersAnalyticsResponse:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        cache_key = self._cache_key("orders", company_id, window, limit)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return OrdersAnalyticsResponse.model_validate(cached)

        payload = OrdersAnalyticsResponse(
            range=self._window_read(window),
            daily=self._daily_orders(company_id, window),
            monthly=self._monthly_orders(company_id, window),
            status_breakdown=self._orders_status_breakdown(company_id, window),
            recent_orders=self._recent_orders(company_id, window, limit=limit),
        )
        self._cache_set(cache_key, payload.model_dump(mode="json"))
        return payload

    def get_products_analytics(
        self,
        company_id: UUID,
        *,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> ProductsAnalyticsResponse:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        cache_key = self._cache_key("products", company_id, window, limit)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return ProductsAnalyticsResponse.model_validate(cached)

        payload = ProductsAnalyticsResponse(
            range=self._window_read(window),
            top_products=self._top_products(company_id, window, limit=limit),
            top_categories=self._top_categories(company_id, window, limit=limit),
            inventory_summary=self._inventory_summary(company_id),
        )
        self._cache_set(cache_key, payload.model_dump(mode="json"))
        return payload

    def get_customers_analytics(
        self,
        company_id: UUID,
        *,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 10,
    ) -> CustomersAnalyticsResponse:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        cache_key = self._cache_key("customers", company_id, window, limit)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return CustomersAnalyticsResponse.model_validate(cached)

        payload = CustomersAnalyticsResponse(
            range=self._window_read(window),
            top_customers=self._top_customers(company_id, window, limit=limit),
            recent_orders=self._recent_orders(company_id, window, limit=limit),
        )
        self._cache_set(cache_key, payload.model_dump(mode="json"))
        return payload

    def export_analytics(
        self,
        company_id: UUID,
        *,
        export_format: AnalyticsExportFormat,
        preset: AnalyticsPreset = "last_30_days",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[bytes, str, str]:
        company = self._get_company(company_id)
        window = self._resolve_window(company.timezone, preset, start_date, end_date)
        dashboard = self._build_dashboard(company_id, company, window)
        revenue = self.get_revenue_analytics(
            company_id,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
        )
        orders = self.get_orders_analytics(
            company_id,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
        )
        products = self.get_products_analytics(
            company_id,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
        )
        customers = self.get_customers_analytics(
            company_id,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
        )

        if export_format == "csv":
            return self._export_csv(dashboard, revenue, orders, products, customers, window)
        if export_format == "excel":
            return self._export_excel(dashboard, revenue, orders, products, customers, window)
        if export_format == "pdf":
            return self._export_pdf(company, dashboard, revenue, orders, products, customers, window)
        raise ValidationAppError("Unsupported export format")

    def _build_dashboard(self, company_id: UUID, company: Company, window: AnalyticsWindow) -> DashboardResponse:
        return DashboardResponse(
            range=self._window_read(window),
            metrics=self._dashboard_metrics(company_id, company, window),
            revenue_by_day=self._daily_revenue(company_id, window),
            orders_by_day=self._daily_orders(company_id, window),
            top_products=self._top_products(company_id, window),
            top_categories=self._top_categories(company_id, window),
            top_customers=self._top_customers(company_id, window),
            recent_orders=self._recent_orders(company_id, window),
            inventory_summary=self._inventory_summary(company_id),
        )

    def _dashboard_metrics(self, company_id: UUID, company: Company, window: AnalyticsWindow) -> DashboardMetricsRead:
        today_window = self._relative_window(company.timezone, days_back=0, anchor="today")
        week_window = self._relative_window(company.timezone, days_back=6, anchor="today")
        month_window = self._relative_window(company.timezone, days_back=29, anchor="today")

        return DashboardMetricsRead(
            today_revenue=self._sum_revenue(company_id, today_window),
            week_revenue=self._sum_revenue(company_id, week_window),
            month_revenue=self._sum_revenue(company_id, month_window),
            today_orders=self._count_orders(company_id, today_window),
            week_orders=self._count_orders(company_id, week_window),
            month_orders=self._count_orders(company_id, month_window),
            average_invoice=self._average_invoice(company_id, window),
            total_products=self._count_products(company_id),
            low_stock_products=self._count_low_stock_products(company_id),
            out_of_stock_products=self._count_out_of_stock_products(company_id),
        )

    def _daily_revenue(self, company_id: UUID, window: AnalyticsWindow) -> list[AnalyticsSeriesPointRead]:
        rows = self.session.execute(
            select(
                func.date_trunc("day", Order.created_at).label("bucket"),
                func.coalesce(func.sum(Order.total), 0).label("value"),
            )
            .where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("bucket")
            .order_by("bucket")
        ).all()
        return self._fill_series(window, rows, "day")

    def _monthly_revenue(self, company_id: UUID, window: AnalyticsWindow) -> list[AnalyticsSeriesPointRead]:
        rows = self.session.execute(
            select(
                func.date_trunc("month", Order.created_at).label("bucket"),
                func.coalesce(func.sum(Order.total), 0).label("value"),
            )
            .where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("bucket")
            .order_by("bucket")
        ).all()
        return self._fill_series(window, rows, "month")

    def _daily_orders(self, company_id: UUID, window: AnalyticsWindow) -> list[AnalyticsSeriesPointRead]:
        rows = self.session.execute(
            select(
                func.date_trunc("day", Order.created_at).label("bucket"),
                func.count(Order.id).label("value"),
            )
            .where(
                Order.company_id == company_id,
                Order.status.in_((ORDER_STATUS_NEW, ORDER_STATUS_CONFIRMED)),
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("bucket")
            .order_by("bucket")
        ).all()
        return self._fill_series(window, rows, "day")

    def _monthly_orders(self, company_id: UUID, window: AnalyticsWindow) -> list[AnalyticsSeriesPointRead]:
        rows = self.session.execute(
            select(
                func.date_trunc("month", Order.created_at).label("bucket"),
                func.count(Order.id).label("value"),
            )
            .where(
                Order.company_id == company_id,
                Order.status.in_((ORDER_STATUS_NEW, ORDER_STATUS_CONFIRMED)),
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("bucket")
            .order_by("bucket")
        ).all()
        return self._fill_series(window, rows, "month")

    def _orders_status_breakdown(self, company_id: UUID, window: AnalyticsWindow) -> AnalyticsStatusBreakdownRead:
        rows = self.session.execute(
            select(
                func.count().filter(Order.status == ORDER_STATUS_NEW),
                func.count().filter(Order.status == ORDER_STATUS_CONFIRMED),
                func.count().filter(Order.status == ORDER_STATUS_DELETED),
                func.coalesce(func.avg(case((Order.status == ORDER_STATUS_CONFIRMED, Order.total), else_=None)), 0),
                func.coalesce(func.max(case((Order.status == ORDER_STATUS_CONFIRMED, Order.total), else_=None)), 0),
            )
            .where(
                Order.company_id == company_id,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
        ).one()
        return AnalyticsStatusBreakdownRead(
            new_orders=int(rows[0] or 0),
            confirmed_orders=int(rows[1] or 0),
            deleted_orders=int(rows[2] or 0),
            average_order_value=self._decimal(rows[4]),
            largest_order=self._decimal(rows[5]),
        )

    def _recent_orders(
        self,
        company_id: UUID,
        window: AnalyticsWindow,
        *,
        limit: int = 10,
    ) -> list[AnalyticsRecentOrderRead]:
        rows = self.session.execute(
            select(Order)
            .where(
                Order.company_id == company_id,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        ).scalars().all()
        return [
            AnalyticsRecentOrderRead(
                id=order.id,
                invoice_number=order.invoice_number,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                status=order.status,
                total=order.total,
                created_at=order.created_at,
            )
            for order in rows
        ]

    def _top_products(
        self,
        company_id: UUID,
        window: AnalyticsWindow,
        *,
        limit: int = 10,
    ) -> list[AnalyticsTopProductRead]:
        rows = self.session.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                Product.unit,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity_sold"),
                func.coalesce(func.sum(OrderItem.line_total), 0).label("revenue"),
                func.count(func.distinct(Order.id)).label("order_count"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .outerjoin(Product, Product.id == OrderItem.product_id)
            .where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by(Product.id, Product.name, Product.sku, Product.unit)
            .order_by(sa.desc("quantity_sold"), sa.desc("revenue"))
            .limit(limit)
        ).all()
        return [
            AnalyticsTopProductRead(
                product_id=row[0],
                product_name=row[1] or "Unknown product",
                sku=row[2],
                unit=row[3],
                quantity_sold=self._decimal(row[4]),
                revenue=self._decimal(row[5]),
                order_count=int(row[6] or 0),
            )
            for row in rows
        ]

    def _top_categories(
        self,
        company_id: UUID,
        window: AnalyticsWindow,
        *,
        limit: int = 10,
    ) -> list[AnalyticsTopCategoryRead]:
        rows = self.session.execute(
            select(
                func.coalesce(Product.category, ProductCategory.name, "Uncategorized").label("category_name"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity_sold"),
                func.coalesce(func.sum(OrderItem.line_total), 0).label("revenue"),
                func.count(func.distinct(Product.id)).label("product_count"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .outerjoin(Product, Product.id == OrderItem.product_id)
            .outerjoin(ProductCategory, ProductCategory.id == Product.category_id)
            .where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("category_name")
            .order_by(sa.desc("quantity_sold"), sa.desc("revenue"))
            .limit(limit)
        ).all()
        return [
            AnalyticsTopCategoryRead(
                category_name=row[0],
                quantity_sold=self._decimal(row[1]),
                revenue=self._decimal(row[2]),
                product_count=int(row[3] or 0),
            )
            for row in rows
        ]

    def _top_customers(
        self,
        company_id: UUID,
        window: AnalyticsWindow,
        *,
        limit: int = 10,
    ) -> list[AnalyticsTopCustomerRead]:
        rows = self.session.execute(
            select(
                func.coalesce(Order.customer_name, "Unknown customer").label("customer_name"),
                Order.customer_phone,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total), 0).label("revenue"),
                func.max(Order.created_at).label("last_order_at"),
            )
            .where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
            .group_by("customer_name", Order.customer_phone)
            .order_by(sa.desc("revenue"), sa.desc("order_count"))
            .limit(limit)
        ).all()
        return [
            AnalyticsTopCustomerRead(
                customer_name=row[0],
                customer_phone=row[1],
                order_count=int(row[2] or 0),
                revenue=self._decimal(row[3]),
                last_order_at=row[4],
            )
            for row in rows
        ]

    def _inventory_summary(self, company_id: UUID) -> InventorySummaryRead:
        total_products = self._count_products(company_id)
        low_stock_products = self._count_low_stock_products(company_id)
        out_of_stock_products = self._count_out_of_stock_products(company_id)
        inventory_value = self.session.scalar(
            select(
                func.coalesce(
                    func.sum(func.coalesce(Product.stock_qty, 0) * func.coalesce(Product.cost, Product.price, 0)),
                    0,
                )
            ).where(Product.company_id == company_id, Product.deleted_at.is_(None))
        )
        return InventorySummaryRead(
            total_products=total_products,
            low_stock_products=low_stock_products,
            out_of_stock_products=out_of_stock_products,
            inventory_value=self._decimal(inventory_value),
        )

    def _sum_revenue(self, company_id: UUID, window: AnalyticsWindow) -> Decimal:
        value = self.session.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
        )
        return self._decimal(value)

    def _count_orders(self, company_id: UUID, window: AnalyticsWindow) -> int:
        value = self.session.scalar(
            select(func.count(Order.id)).where(
                Order.company_id == company_id,
                Order.status.in_((ORDER_STATUS_NEW, ORDER_STATUS_CONFIRMED)),
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
        )
        return int(value or 0)

    def _average_invoice(self, company_id: UUID, window: AnalyticsWindow) -> Decimal:
        value = self.session.scalar(
            select(func.coalesce(func.avg(Order.total), 0)).where(
                Order.company_id == company_id,
                Order.status == ORDER_STATUS_CONFIRMED,
                Order.created_at >= window.start_at,
                Order.created_at < window.end_at,
            )
        )
        return self._decimal(value)

    def _count_products(self, company_id: UUID) -> int:
        value = self.session.scalar(
            select(func.count(Product.id)).where(Product.company_id == company_id, Product.deleted_at.is_(None))
        )
        return int(value or 0)

    def _count_low_stock_products(self, company_id: UUID) -> int:
        value = self.session.scalar(
            select(func.count(Product.id)).where(
                Product.company_id == company_id,
                Product.deleted_at.is_(None),
                Product.stock_qty.is_not(None),
                Product.low_stock_threshold.is_not(None),
                Product.stock_qty <= Product.low_stock_threshold,
                Product.stock_qty > 0,
            )
        )
        return int(value or 0)

    def _count_out_of_stock_products(self, company_id: UUID) -> int:
        value = self.session.scalar(
            select(func.count(Product.id)).where(
                Product.company_id == company_id,
                Product.deleted_at.is_(None),
                or_(Product.stock_qty.is_(None), Product.stock_qty <= 0),
            )
        )
        return int(value or 0)

    def _fill_series(
        self,
        window: AnalyticsWindow,
        rows,
        granularity: str,
    ) -> list[AnalyticsSeriesPointRead]:
        values: dict[str, Decimal] = {}
        for bucket, raw_value in rows:
            local_bucket = self._to_timezone(bucket, window.timezone)
            key = local_bucket.strftime("%Y-%m") if granularity == "month" else local_bucket.strftime("%Y-%m-%d")
            values[key] = self._decimal(raw_value)

        points: list[AnalyticsSeriesPointRead] = []
        if granularity == "month":
            current = date(window.start_date.year, window.start_date.month, 1)
            end = date(window.end_date.year, window.end_date.month, 1)
            while current <= end:
                key = current.strftime("%Y-%m")
                points.append(AnalyticsSeriesPointRead(label=key, value=values.get(key, Decimal("0")), count=0))
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
            return points

        current = window.start_date
        while current <= window.end_date:
            key = current.strftime("%Y-%m-%d")
            points.append(AnalyticsSeriesPointRead(label=key, value=values.get(key, Decimal("0")), count=0))
            current += timedelta(days=1)
        return points

    def _window_read(self, window: AnalyticsWindow) -> AnalyticsRangeRead:
        return AnalyticsRangeRead(
            preset=window.preset,
            start_date=window.start_date,
            end_date=window.end_date,
            timezone=window.timezone,
        )

    def _resolve_window(
        self,
        company_timezone: str,
        preset: AnalyticsPreset,
        start_date: date | None,
        end_date: date | None,
    ) -> AnalyticsWindow:
        tz = self._timezone(company_timezone)
        now = datetime.now(tz)
        if preset == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif preset == "yesterday":
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = today_start - timedelta(days=1)
            end = today_start
        elif preset == "last_7_days":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
            end = now
        elif preset == "last_30_days":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29)
            end = now
        elif preset == "this_month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif preset == "last_month":
            this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start = (this_month_start - timedelta(days=1)).replace(day=1)
            end = this_month_start
        else:
            raise ValidationAppError("Unsupported analytics preset")

        if start_date is not None or end_date is not None:
            if start_date is None or end_date is None:
                raise ValidationAppError("start_date and end_date are required for custom ranges")
            start = datetime.combine(start_date, time_obj.min, tzinfo=tz)
            end = datetime.combine(end_date + timedelta(days=1), time_obj.min, tzinfo=tz)

        if end <= start:
            raise ValidationAppError("Invalid analytics date range")

        return AnalyticsWindow(
            preset=preset,
            timezone=company_timezone,
            start_at=start.astimezone(timezone.utc),
            end_at=end.astimezone(timezone.utc),
            start_date=start.astimezone(tz).date(),
            end_date=(end - timedelta(seconds=1)).astimezone(tz).date(),
        )

    def _relative_window(self, company_timezone: str, *, days_back: int, anchor: str) -> AnalyticsWindow:
        if anchor != "today":
            raise ValidationAppError("Unsupported analytics anchor")
        tz = self._timezone(company_timezone)
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_back)
        end = now
        return AnalyticsWindow(
            preset="last_7_days" if days_back == 6 else "last_30_days" if days_back == 29 else "today",
            timezone=company_timezone,
            start_at=start.astimezone(timezone.utc),
            end_at=end.astimezone(timezone.utc),
            start_date=start.date(),
            end_date=end.date(),
        )

    def _timezone(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except Exception as exc:
            raise ValidationAppError("Company timezone is invalid") from exc

    def _to_timezone(self, value: datetime, timezone_name: str) -> datetime:
        tz = self._timezone(timezone_name)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(tz)

    def _decimal(self, value: object) -> Decimal:
        if value is None:
            return Decimal("0.00")
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _get_company(self, company_id: UUID) -> Company:
        company = self.session.get(Company, company_id)
        if company is None or company.deleted_at is not None:
            raise NotFoundError("Company not found")
        return company

    def _cache_key(self, kind: str, company_id: UUID, window: AnalyticsWindow, *extra: object) -> str:
        parts = [
            kind,
            str(company_id),
            window.preset,
            window.timezone,
            window.start_at.isoformat(),
            window.end_at.isoformat(),
            *[str(item) for item in extra],
        ]
        return ":".join(parts)

    def _cache_get(self, key: str) -> object | None:
        now = time.monotonic()
        with _CACHE_LOCK:
            entry = _ANALYTICS_CACHE.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                _ANALYTICS_CACHE.pop(key, None)
                return None
            return value

    def _cache_set(self, key: str, value: object) -> None:
        with _CACHE_LOCK:
            _ANALYTICS_CACHE[key] = (time.monotonic() + _CACHE_TTL_SECONDS, value)

    def _export_csv(
        self,
        dashboard: DashboardResponse,
        revenue: RevenueAnalyticsResponse,
        orders: OrdersAnalyticsResponse,
        products: ProductsAnalyticsResponse,
        customers: CustomersAnalyticsResponse,
        window: AnalyticsWindow,
    ) -> tuple[bytes, str, str]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Kara Orders Analytics Export"])
        writer.writerow(["Range", window.start_date.isoformat(), window.end_date.isoformat()])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        for label, value in [
            ("Today revenue", dashboard.metrics.today_revenue),
            ("Week revenue", dashboard.metrics.week_revenue),
            ("Month revenue", dashboard.metrics.month_revenue),
            ("Average invoice", dashboard.metrics.average_invoice),
            ("Total products", dashboard.metrics.total_products),
        ]:
            writer.writerow([label, value])
        writer.writerow([])
        writer.writerow(["Top products"])
        writer.writerow(["Name", "SKU", "Quantity sold", "Revenue", "Orders"])
        for item in products.top_products:
            writer.writerow([item.product_name, item.sku, item.quantity_sold, item.revenue, item.order_count])
        return buffer.getvalue().encode("utf-8"), "text/csv; charset=utf-8", "analytics.csv"

    def _export_excel(
        self,
        dashboard: DashboardResponse,
        revenue: RevenueAnalyticsResponse,
        orders: OrdersAnalyticsResponse,
        products: ProductsAnalyticsResponse,
        customers: CustomersAnalyticsResponse,
        window: AnalyticsWindow,
    ) -> tuple[bytes, str, str]:
        buffer = io.BytesIO()
        workbook = Workbook(buffer, {"in_memory": True})
        money_fmt = workbook.add_format({"num_format": "#,##0.00"})
        number_fmt = workbook.add_format({"num_format": "0"})

        summary = workbook.add_worksheet("Summary")
        summary.write_row(0, 0, ["Metric", "Value"])
        for idx, (label, value) in enumerate(
            [
                ("Today revenue", dashboard.metrics.today_revenue),
                ("Week revenue", dashboard.metrics.week_revenue),
                ("Month revenue", dashboard.metrics.month_revenue),
                ("Average invoice", dashboard.metrics.average_invoice),
                ("Total products", dashboard.metrics.total_products),
                ("Low stock products", dashboard.metrics.low_stock_products),
                ("Out of stock products", dashboard.metrics.out_of_stock_products),
            ],
            start=1,
        ):
            summary.write(idx, 0, label)
            summary.write_number(idx, 1, float(value), money_fmt if isinstance(value, Decimal) else number_fmt)

        revenue_sheet = workbook.add_worksheet("Revenue")
        revenue_sheet.write_row(0, 0, ["Label", "Value"])
        for idx, point in enumerate(revenue.daily, start=1):
            revenue_sheet.write(idx, 0, point.label)
            revenue_sheet.write_number(idx, 1, float(point.value), money_fmt)

        orders_sheet = workbook.add_worksheet("Orders")
        orders_sheet.write_row(0, 0, ["Label", "Value"])
        for idx, point in enumerate(orders.daily, start=1):
            orders_sheet.write(idx, 0, point.label)
            orders_sheet.write_number(idx, 1, float(point.value), number_fmt)

        products_sheet = workbook.add_worksheet("Products")
        products_sheet.write_row(0, 0, ["Product", "SKU", "Quantity sold", "Revenue", "Orders"])
        for idx, item in enumerate(products.top_products, start=1):
            products_sheet.write_row(idx, 0, [item.product_name, item.sku, float(item.quantity_sold), float(item.revenue), item.order_count])

        customers_sheet = workbook.add_worksheet("Customers")
        customers_sheet.write_row(0, 0, ["Customer", "Phone", "Orders", "Revenue", "Last order"])
        for idx, item in enumerate(customers.top_customers, start=1):
            customers_sheet.write_row(
                idx,
                0,
                [
                    item.customer_name,
                    item.customer_phone,
                    item.order_count,
                    float(item.revenue),
                    item.last_order_at.isoformat(),
                ],
            )

        workbook.close()
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "analytics.xlsx"

    def _export_pdf(
        self,
        company: Company,
        dashboard: DashboardResponse,
        revenue: RevenueAnalyticsResponse,
        orders: OrdersAnalyticsResponse,
        products: ProductsAnalyticsResponse,
        customers: CustomersAnalyticsResponse,
        window: AnalyticsWindow,
    ) -> tuple[bytes, str, str]:
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Analytics Export",
            author=company.name,
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="AnalyticsTitle", parent=styles["Title"], fontSize=20, leading=24))
        styles.add(ParagraphStyle(name="AnalyticsBody", parent=styles["BodyText"], fontSize=9, leading=12))
        elements: list[object] = [
            Paragraph(f"{company.name} Analytics", styles["AnalyticsTitle"]),
            Paragraph(
                f"Range: {window.start_date.isoformat()} → {window.end_date.isoformat()}",
                styles["AnalyticsBody"],
            ),
            Spacer(1, 8),
        ]

        metric_rows = [["Metric", "Value"]]
        for label, value in [
            ("Today revenue", dashboard.metrics.today_revenue),
            ("Week revenue", dashboard.metrics.week_revenue),
            ("Month revenue", dashboard.metrics.month_revenue),
            ("Average invoice", dashboard.metrics.average_invoice),
            ("Total products", dashboard.metrics.total_products),
        ]:
            metric_rows.append([label, str(value)])
        metric_table = Table(metric_rows, colWidths=[90 * mm, 50 * mm])
        metric_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db"))]))
        elements.append(metric_table)
        elements.append(Spacer(1, 10))

        product_rows = [["Top products", "Qty", "Revenue"]]
        for item in products.top_products[:8]:
            product_rows.append([item.product_name, str(item.quantity_sold), str(item.revenue)])
        product_table = Table(product_rows, colWidths=[90 * mm, 25 * mm, 25 * mm])
        product_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db"))]))
        elements.append(product_table)

        document.build(elements)
        return buffer.getvalue(), "application/pdf", "analytics.pdf"
