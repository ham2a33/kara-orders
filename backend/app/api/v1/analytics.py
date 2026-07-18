from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.deps import get_app_settings, get_db
from app.db.models.user import User
from app.schemas.analytics import (
    AnalyticsExportFormat,
    AnalyticsPreset,
    CustomersAnalyticsResponse,
    DashboardResponse,
    OrdersAnalyticsResponse,
    ProductsAnalyticsResponse,
    RevenueAnalyticsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


def _service(session: Session, settings: Settings) -> AnalyticsService:
    return AnalyticsService(session=session, settings=settings)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> DashboardResponse:
    return _service(session, settings).get_dashboard(
        current_user.company_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/analytics/revenue", response_model=RevenueAnalyticsResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN, Role.MANAGER))])
def get_revenue_analytics(
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> RevenueAnalyticsResponse:
    return _service(session, settings).get_revenue_analytics(
        current_user.company_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/analytics/orders", response_model=OrdersAnalyticsResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN, Role.MANAGER))])
def get_orders_analytics(
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> OrdersAnalyticsResponse:
    return _service(session, settings).get_orders_analytics(
        current_user.company_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/analytics/products", response_model=ProductsAnalyticsResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN, Role.MANAGER))])
def get_products_analytics(
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProductsAnalyticsResponse:
    return _service(session, settings).get_products_analytics(
        current_user.company_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/analytics/customers", response_model=CustomersAnalyticsResponse, dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN, Role.MANAGER))])
def get_customers_analytics(
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CustomersAnalyticsResponse:
    return _service(session, settings).get_customers_analytics(
        current_user.company_id,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/analytics/export", dependencies=[Depends(require_roles(Role.OWNER, Role.ADMIN, Role.MANAGER))])
def export_analytics(
    format: AnalyticsExportFormat = "csv",
    preset: AnalyticsPreset = "last_30_days",
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> Response:
    content, content_type, filename = _service(session, settings).export_analytics(
        current_user.company_id,
        export_format=format,  # type: ignore[arg-type]
        preset=preset,
        start_date=start_date,
        end_date=end_date,
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
